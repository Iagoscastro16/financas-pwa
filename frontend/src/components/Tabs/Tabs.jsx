import "./Tabs.css";

export default function Tabs({ tabs, activeTab, onChange }) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          type="button"
          role="tab"
          aria-selected={tab.value === activeTab}
          className={`tabs__button ${
            tab.value === activeTab ? "tabs__button--active" : ""
          }`}
          onClick={() => onChange(tab.value)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
