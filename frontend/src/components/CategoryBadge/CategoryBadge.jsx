import "./CategoryBadge.css";

export default function CategoryBadge({ categoria }) {
  return (
    <span className={`category-badge category-badge--${categoria.tipo}`}>
      <span className="category-badge__dot" aria-hidden="true" />
      {categoria.nome}
    </span>
  );
}
