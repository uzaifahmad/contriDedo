BEGIN;

CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL,
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX users_email_lower_unique_idx
    ON users (LOWER(email));

CREATE TABLE trips (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    created_by BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expenses (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    payer_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    total_amount NUMERIC(12, 2) NOT NULL CHECK (total_amount > 0),
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX expenses_trip_id_idx ON expenses (trip_id);
CREATE INDEX expenses_payer_id_idx ON expenses (payer_id);

CREATE TABLE expense_splits (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    expense_id BIGINT NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    amount_owed NUMERIC(12, 2) NOT NULL CHECK (amount_owed >= 0),
    calculation_method TEXT NOT NULL
        CHECK (calculation_method IN ('equal', 'percentage', 'exact')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (expense_id, user_id)
);

CREATE INDEX expense_splits_user_id_idx ON expense_splits (user_id);

COMMIT;
