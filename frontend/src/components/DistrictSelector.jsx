export default function DistrictSelector({ districts, selected, onSelect }) {
  return (
    <div className="district-row" role="group" aria-label="Select district dialect">
      {districts.map((d) => (
        <button
          key={d}
          type="button"
          className={`district-pill${d === selected ? ' active' : ''}`}
          onClick={() => onSelect(d)}
          aria-pressed={d === selected}
        >
          {d}
        </button>
      ))}
    </div>
  )
}
