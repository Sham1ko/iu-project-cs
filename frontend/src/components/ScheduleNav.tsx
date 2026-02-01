type NavItem = {
  id: string;
  label: string;
};

type ScheduleNavProps = {
  items: NavItem[];
  title?: string;
};

export default function ScheduleNav({ items, title = "On This Page" }: ScheduleNavProps) {
  return (
    <nav className="panel schedule-nav" aria-label={title}>
      <div className="schedule-nav-title">{title}</div>
      <div className="schedule-nav-list">
        {items.map((item) => (
          <a key={item.id} href={`#${item.id}`}>
            {item.label}
          </a>
        ))}
      </div>
    </nav>
  );
}
