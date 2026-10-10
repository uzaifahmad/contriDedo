"""Create the initial API schema."""

from alembic import op

from contri_dedo.models import Base

revision = "0001_backend_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION enforce_expense_split_total() RETURNS trigger AS $$
            DECLARE target_expense_id BIGINT;
            BEGIN
                IF TG_TABLE_NAME = 'expenses' THEN
                    IF TG_OP = 'DELETE' THEN
                        target_expense_id := OLD.id;
                    ELSE
                        target_expense_id := NEW.id;
                    END IF;
                ELSE
                    IF TG_OP = 'DELETE' THEN
                        target_expense_id := OLD.expense_id;
                    ELSE
                        target_expense_id := NEW.expense_id;
                    END IF;
                END IF;

                IF EXISTS (SELECT 1 FROM expenses WHERE id = target_expense_id)
                   AND (SELECT COALESCE(SUM(amount_owed), 0) FROM expense_splits WHERE expense_id = target_expense_id)
                       <> (SELECT total_amount FROM expenses WHERE id = target_expense_id) THEN
                    RAISE EXCEPTION 'Expense split amounts must equal the expense total';
                END IF;
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql
            """
        )
        op.execute(
            """
            CREATE CONSTRAINT TRIGGER expense_split_total_from_expense
            AFTER INSERT OR UPDATE OR DELETE ON expenses
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION enforce_expense_split_total()
            """
        )
        op.execute(
            """
            CREATE CONSTRAINT TRIGGER expense_split_total_from_split
            AFTER INSERT OR UPDATE OR DELETE ON expense_splits
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION enforce_expense_split_total()
            """
        )


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS enforce_expense_split_total()")