import { Link } from "react-router-dom";

export default function Brand({ light = false }: { light?: boolean }) {
  return (
    <Link
      aria-label="contriDedo home"
      className={`brand ${light ? "brand-light" : ""}`}
      to="/"
    >
      <span aria-hidden="true" className="brand-mark">
        c
      </span>
      <span className="brand-name">
        contri<span>Dedo</span>
      </span>
    </Link>
  );
}
