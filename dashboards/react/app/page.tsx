"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Row = Record<string, string>;

const number = (value?: string) => Number(value ?? 0) || 0;

function parseCsv(text: string): Row[] {
  const [header, ...lines] = text.trim().split(/\r?\n/);
  if (!header) return [];
  const columns = header.split(",").map((value) => value.toLowerCase());
  return lines.map((line) => {
    const values = line.match(/(?:[^,"]+|"(?:[^"]|"")*")+/g) ?? [];
    return Object.fromEntries(columns.map((column, index) => [column, (values[index] ?? "").replace(/^"|"$/g, "").replace(/""/g, '"')]));
  });
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return <article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5">
    <p className="text-xs font-bold uppercase tracking-[.15em] text-[#a8b5c7]">{label}</p>
    <p className="mt-3 text-3xl font-black tracking-tight text-white">{value}</p>
    <p className="mt-2 text-sm text-[#a8b5c7]">{note}</p>
  </article>;
}

function Standings({ title, rows, name }: { title: string; rows: Row[]; name: string }) {
  return <article className="overflow-hidden rounded-2xl border border-[#22354f] bg-[#0e1b2d]">
    <div className="flex items-center justify-between border-b border-[#22354f] px-5 py-4">
      <h3 className="font-bold">{title}</h3><span className="text-xs text-[#a8b5c7]">Latest standings</span>
    </div>
    <div className="divide-y divide-[#22354f]">
      {rows.slice(0, 8).map((row, index) => <div key={row[name] + "-" + index} className="grid grid-cols-[2.5rem_1fr_auto] items-center gap-3 px-5 py-3">
        <span className="font-black text-[#35c2ff]">{row.championship_position || "—"}</span>
        <span className="font-medium">{row[name]}</span>
        <span className="text-sm text-[#a8b5c7]">{number(row.championship_points)} pts</span>
      </div>)}
    </div>
  </article>;
}

function ViewButton({ active, children, onClick }: { active: boolean; children: string; onClick: () => void }) {
  return <button type="button" onClick={onClick} className={"rounded-full px-4 py-2 text-sm font-bold transition " + (active ? "bg-[#e10600] text-white" : "bg-[#13243a] text-[#a8b5c7] hover:bg-[#22354f]")}>{children}</button>;
}

function SimpleTable({ rows, columns }: { rows: Row[]; columns: Array<{ key: string; label: string }> }) {
  return <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b border-[#22354f] text-xs uppercase tracking-[.12em] text-[#a8b5c7]"><tr>{columns.map((column) => <th key={column.key} className="px-4 py-3 font-bold">{column.label}</th>)}</tr></thead><tbody className="divide-y divide-[#22354f]">{rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column.key} className="px-4 py-3">{row[column.key] || "—"}</td>)}</tr>)}</tbody></table></div>;
}

export default function Home() {
  const [races, setRaces] = useState<Row[]>([]);
  const [drivers, setDrivers] = useState<Row[]>([]);
  const [constructors, setConstructors] = useState<Row[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "empty">("loading");
  const [season, setSeason] = useState("");
  const [view, setView] = useState<"overview" | "drivers" | "races" | "constructors" | "circuits" | "headToHead" | "history">("overview");
  const [selectedDriverId, setSelectedDriverId] = useState("");
  const [comparisonDriverId, setComparisonDriverId] = useState("");
  const [selectedRound, setSelectedRound] = useState("");
  const [selectedConstructorId, setSelectedConstructorId] = useState("");
  const [historicalSeasonA, setHistoricalSeasonA] = useState("");
  const [historicalSeasonB, setHistoricalSeasonB] = useState("");

  useEffect(() => {
    Promise.all([
      fetch("data/driver_race_performance.csv").then((r) => r.ok ? r.text() : ""),
      fetch("data/driver_championship_progression.csv").then((r) => r.ok ? r.text() : ""),
      fetch("data/constructor_championship_progression.csv").then((r) => r.ok ? r.text() : ""),
    ]).then(([raceText, driverText, constructorText]) => {
      const nextRaces = parseCsv(raceText);
      setRaces(nextRaces); setDrivers(parseCsv(driverText)); setConstructors(parseCsv(constructorText));
      setSeason([...new Set(nextRaces.map((row) => row.season).filter(Boolean))].sort().at(-1) ?? "");
      setStatus(nextRaces.length ? "ready" : "empty");
    }).catch(() => setStatus("empty"));
  }, []);

  const seasons = useMemo(() => [...new Set(races.map((row) => row.season).filter(Boolean))].sort().reverse(), [races]);
  const seasonRaces = races.filter((row) => row.season === season);
  const seasonDrivers = drivers.filter((row) => row.season === season);
  const seasonConstructors = constructors.filter((row) => row.season === season);
  const round = Math.max(...seasonRaces.map((row) => number(row.round_number)), 0);
  const driverRound = Math.max(...seasonDrivers.map((row) => number(row.round_number)), 0);
  const constructorRound = Math.max(...seasonConstructors.map((row) => number(row.round_number)), 0);
  const latestDrivers = seasonDrivers.filter((row) => number(row.round_number) === driverRound).sort((a, b) => number(a.championship_position) - number(b.championship_position));
  const latestConstructors = seasonConstructors.filter((row) => number(row.round_number) === constructorRound).sort((a, b) => number(a.championship_position) - number(b.championship_position));
  const pointsByRound = Array.from({ length: round }, (_, index) => {
    const currentRound = index + 1;
    return { round: "R" + currentRound, points: seasonRaces.filter((row) => number(row.round_number) === currentRound).reduce((sum, row) => sum + number(row.points), 0) };
  });
  const constructorChart = latestConstructors.slice(0, 6).map((row) => ({ name: row.constructor_name, points: number(row.championship_points) }));
  const leader = latestDrivers[0];
  const selectedDriver = latestDrivers.find((row) => row.driver_id === selectedDriverId) ?? leader;
  const selectedConstructor = latestConstructors.find((row) => row.constructor_id === selectedConstructorId) ?? latestConstructors[0];
  const selectedRaceRound = number(selectedRound) || round;
  const selectedRaceResults = seasonRaces.filter((row) => number(row.round_number) === selectedRaceRound).sort((a, b) => number(a.finishing_position) - number(b.finishing_position));
  const driverTrend = seasonDrivers.filter((row) => row.driver_id === selectedDriver?.driver_id).map((row) => ({ round: "R" + row.round_number, points: number(row.championship_points), position: number(row.championship_position) }));
  const constructorTrend = seasonConstructors.filter((row) => row.constructor_id === selectedConstructor?.constructor_id).map((row) => ({ round: "R" + row.round_number, points: number(row.championship_points), position: number(row.championship_position) }));
  const comparisonDriver = latestDrivers.find((row) => row.driver_id === comparisonDriverId) ?? latestDrivers[1] ?? leader;
  const headToHead = Array.from({ length: Math.max(driverRound, 0) }, (_, index) => {
    const currentRound = index + 1;
    const first = seasonDrivers.find((row) => row.driver_id === selectedDriver?.driver_id && number(row.round_number) === currentRound);
    const second = seasonDrivers.find((row) => row.driver_id === comparisonDriver?.driver_id && number(row.round_number) === currentRound);
    return { round: "R" + currentRound, [selectedDriver?.driver_name ?? "Driver A"]: number(first?.championship_points), [comparisonDriver?.driver_name ?? "Driver B"]: number(second?.championship_points) };
  });
  const driverCircuitRows = Array.from(new Set(seasonRaces.map((row) => row.circuit_name).filter(Boolean))).map((circuit) => {
    const results = seasonRaces.filter((row) => row.driver_id === selectedDriver?.driver_id && row.circuit_name === circuit);
    return { circuit_name: circuit, races: String(results.length), average_finish: results.length ? (results.reduce((sum, row) => sum + number(row.finishing_position), 0) / results.length).toFixed(1) : "—", points: String(results.reduce((sum, row) => sum + number(row.points), 0)) };
  }).filter((row) => number(row.races)).sort((a, b) => number(b.points) - number(a.points));
  const seasonA = historicalSeasonA || season;
  const seasonB = historicalSeasonB || seasons.find((value) => value !== season) || season;
  const seasonSummary = (value: string) => {
    const records = races.filter((row) => row.season === value);
    const totalPoints = records.reduce((sum, row) => sum + number(row.points), 0);
    const winner = records.filter((row) => number(row.finishing_position) === 1).reduce<Record<string, number>>((result, row) => ({ ...result, [row.driver_name]: (result[row.driver_name] ?? 0) + 1 }), {});
    const leadingWinner = Object.entries(winner).sort(([, first], [, second]) => second - first)[0];
    return { season: value, races: String(Math.max(...records.map((row) => number(row.round_number)), 0)), points: String(totalPoints), winner: leadingWinner?.[0] ?? "—", wins: String(leadingWinner?.[1] ?? 0) };
  };
  const historicalRows = [seasonSummary(seasonA), seasonSummary(seasonB)];

  return <main className="min-h-screen bg-[#07111f] text-[#f7f9fc]">
    <header className="border-b border-[#22354f] bg-[#0a1627]/95 px-5 py-5 md:px-10">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-5">
        <div><p className="text-xs font-bold uppercase tracking-[.24em] text-[#35c2ff]">Formula 1 analytics engineering</p><h1 className="mt-1 text-2xl font-black tracking-tight md:text-3xl">Championship Monitor</h1></div>
        <div className="flex items-center gap-3"><span className="rounded-full bg-[#e10600]/15 px-3 py-1 text-xs font-bold text-[#ff7a76]">Curated public extract</span>
          <label className="sr-only" htmlFor="season">Season</label>
          <select id="season" value={season} onChange={(event) => setSeason(event.target.value)} className="rounded-lg border border-[#36516f] bg-[#0e1b2d] px-3 py-2 text-sm font-bold text-white">{seasons.map((value) => <option key={value}>{value}</option>)}</select>
        </div>
      </div>
    </header>
    <section className="mx-auto max-w-7xl px-5 py-8 md:px-10">
      {status === "loading" && <p className="rounded-xl border border-[#22354f] bg-[#0e1b2d] p-6 text-[#a8b5c7]">Loading the latest approved dashboard extract…</p>}
      {status === "empty" && <div className="rounded-2xl border border-dashed border-[#36516f] bg-[#0e1b2d] p-8"><h2 className="text-xl font-bold">Dashboard data is not published yet</h2><p className="mt-2 max-w-2xl text-[#a8b5c7]">Run the approved read-only export with the React output option, then deploy the generated public extract. This browser never connects to Snowflake.</p><code className="mt-5 block overflow-auto rounded-lg bg-[#07111f] p-4 text-sm text-[#35c2ff]">uv run --frozen python scripts/export_dashboard_data.py --react-out-dir dashboards/react/public/data</code></div>}
      {status === "ready" && <><nav aria-label="Dashboard views" className="mb-7 flex flex-wrap gap-2"><ViewButton active={view === "overview"} onClick={() => setView("overview")}>Overview</ViewButton><ViewButton active={view === "drivers"} onClick={() => setView("drivers")}>Driver trend</ViewButton><ViewButton active={view === "headToHead"} onClick={() => setView("headToHead")}>Head-to-head</ViewButton><ViewButton active={view === "races"} onClick={() => setView("races")}>Race analysis</ViewButton><ViewButton active={view === "constructors"} onClick={() => setView("constructors")}>Constructor detail</ViewButton><ViewButton active={view === "circuits"} onClick={() => setView("circuits")}>Circuit trends</ViewButton><ViewButton active={view === "history"} onClick={() => setView("history")}>Season comparison</ViewButton></nav><div className={view === "overview" ? "" : "hidden"}><div className="mb-7 flex flex-wrap items-end justify-between gap-3"><div><p className="text-sm text-[#a8b5c7]">Season {season} · through round {round}</p><h2 className="mt-1 text-3xl font-black tracking-tight">At a glance</h2></div><p className="max-w-md text-right text-sm text-[#a8b5c7]">Data is a Snowflake MARTS snapshot, not live timing.</p></div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Championship leader" value={leader?.driver_name ?? "—"} note={number(leader?.championship_points) + " points"} />
          <Metric label="Races recorded" value={String(round)} note="Current season rounds" />
          <Metric label="Points awarded" value={String(seasonRaces.reduce((sum, row) => sum + number(row.points), 0))} note="Across classified results" />
          <Metric label="Constructors ranked" value={String(latestConstructors.length)} note="Latest published standings" />
        </div>
        <div className="mt-6 grid gap-6 xl:grid-cols-[1.35fr_.9fr]">
          <article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><p className="text-sm font-bold">Points awarded by round</p><p className="mb-5 text-sm text-[#a8b5c7]">Race-week scoring volume.</p><div className="h-72"><ResponsiveContainer width="100%" height="100%"><AreaChart data={pointsByRound}><defs><linearGradient id="points" x1="0" x2="0" y1="0" y2="1"><stop offset="5%" stopColor="#e10600" stopOpacity={0.65}/><stop offset="95%" stopColor="#e10600" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#22354f" vertical={false}/><XAxis dataKey="round" stroke="#a8b5c7" tickLine={false} axisLine={false}/><YAxis stroke="#a8b5c7" tickLine={false} axisLine={false}/><Tooltip contentStyle={{ background: "#07111f", border: "1px solid #36516f", borderRadius: 12 }}/><Area type="monotone" dataKey="points" stroke="#e10600" fill="url(#points)" strokeWidth={3}/></AreaChart></ResponsiveContainer></div></article>
          <article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><p className="text-sm font-bold">Constructor battle</p><p className="mb-5 text-sm text-[#a8b5c7]">Top six teams by championship points.</p><div className="h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={constructorChart} layout="vertical" margin={{ left: 18 }}><CartesianGrid stroke="#22354f" horizontal={false}/><XAxis type="number" stroke="#a8b5c7" tickLine={false} axisLine={false}/><YAxis dataKey="name" type="category" width={105} stroke="#a8b5c7" tickLine={false} axisLine={false}/><Tooltip contentStyle={{ background: "#07111f", border: "1px solid #36516f", borderRadius: 12 }}/><Bar dataKey="points" fill="#35c2ff" radius={[0, 5, 5, 0]}/></BarChart></ResponsiveContainer></div></article>
        </div>
        <div className="mt-6 grid gap-6 xl:grid-cols-2"><Standings title="Driver standings" rows={latestDrivers} name="driver_name" /><Standings title="Constructor standings" rows={latestConstructors} name="constructor_name" /></div></div>
        {view === "drivers" && <section className="grid gap-6 xl:grid-cols-[1.3fr_.7fr]"><article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><div className="flex flex-wrap items-center justify-between gap-4"><div><h2 className="text-xl font-black">Driver comparison</h2><p className="text-sm text-[#a8b5c7]">Championship points and rank by round.</p></div><select value={selectedDriver?.driver_id ?? ""} onChange={(event) => setSelectedDriverId(event.target.value)} className="rounded-lg border border-[#36516f] bg-[#07111f] px-3 py-2 text-sm font-bold text-white">{latestDrivers.map((row) => <option key={row.driver_id} value={row.driver_id}>{row.driver_name}</option>)}</select></div><div className="mt-6 h-80"><ResponsiveContainer width="100%" height="100%"><LineChart data={driverTrend}><CartesianGrid stroke="#22354f" vertical={false}/><XAxis dataKey="round" stroke="#a8b5c7" tickLine={false} axisLine={false}/><YAxis yAxisId="points" stroke="#a8b5c7" tickLine={false} axisLine={false}/><YAxis yAxisId="rank" orientation="right" reversed domain={[1, "dataMax"]} stroke="#facb3d" tickLine={false} axisLine={false}/><Tooltip contentStyle={{ background: "#07111f", border: "1px solid #36516f", borderRadius: 12 }}/><Line yAxisId="points" type="monotone" dataKey="points" stroke="#35c2ff" strokeWidth={3} dot={false}/><Line yAxisId="rank" type="monotone" dataKey="position" stroke="#facb3d" strokeWidth={2} dot={false}/></LineChart></ResponsiveContainer></div></article><article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><h3 className="font-bold">Current driver standings</h3><p className="mb-4 text-sm text-[#a8b5c7]">Select a driver to compare their progression.</p><SimpleTable rows={latestDrivers.slice(0, 10)} columns={[{ key: "championship_position", label: "Rank" }, { key: "driver_name", label: "Driver" }, { key: "championship_points", label: "Points" }]} /></article></section>}
        {view === "headToHead" && <section className="grid gap-6 xl:grid-cols-[1.3fr_.7fr]"><article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-black">Head-to-head</h2><p className="text-sm text-[#a8b5c7]">Cumulative championship points by round.</p></div><div className="flex flex-wrap gap-2"><select value={selectedDriver?.driver_id ?? ""} onChange={(event) => setSelectedDriverId(event.target.value)} className="rounded-lg border border-[#36516f] bg-[#07111f] px-3 py-2 text-sm font-bold text-white">{latestDrivers.map((row) => <option key={row.driver_id} value={row.driver_id}>{row.driver_name}</option>)}</select><select value={comparisonDriver?.driver_id ?? ""} onChange={(event) => setComparisonDriverId(event.target.value)} className="rounded-lg border border-[#36516f] bg-[#07111f] px-3 py-2 text-sm font-bold text-white">{latestDrivers.filter((row) => row.driver_id !== selectedDriver?.driver_id).map((row) => <option key={row.driver_id} value={row.driver_id}>{row.driver_name}</option>)}</select></div></div><div className="mt-6 h-80"><ResponsiveContainer width="100%" height="100%"><LineChart data={headToHead}><CartesianGrid stroke="#22354f" vertical={false}/><XAxis dataKey="round" stroke="#a8b5c7" tickLine={false} axisLine={false}/><YAxis stroke="#a8b5c7" tickLine={false} axisLine={false}/><Tooltip contentStyle={{ background: "#07111f", border: "1px solid #36516f", borderRadius: 12 }}/><Line type="monotone" dataKey={selectedDriver?.driver_name ?? "Driver A"} stroke="#35c2ff" strokeWidth={3} dot={false}/><Line type="monotone" dataKey={comparisonDriver?.driver_name ?? "Driver B"} stroke="#facb3d" strokeWidth={3} dot={false}/></LineChart></ResponsiveContainer></div></article><article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><h3 className="font-bold">Current comparison</h3><div className="mt-5 space-y-4"><Metric label={selectedDriver?.driver_name ?? "Driver A"} value={String(number(selectedDriver?.championship_points))} note={"P" + (selectedDriver?.championship_position ?? "—") + " in championship"}/><Metric label={comparisonDriver?.driver_name ?? "Driver B"} value={String(number(comparisonDriver?.championship_points))} note={"P" + (comparisonDriver?.championship_position ?? "—") + " in championship"}/></div></article></section>}
        {view === "races" && <section className="grid gap-6 xl:grid-cols-[.75fr_1.25fr]"><article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><h2 className="text-xl font-black">Race analysis</h2><p className="mb-5 text-sm text-[#a8b5c7]">Classified results, grid movement, and points for one round.</p><select value={String(selectedRaceRound)} onChange={(event) => setSelectedRound(event.target.value)} className="w-full rounded-lg border border-[#36516f] bg-[#07111f] px-3 py-2 text-sm font-bold text-white">{Array.from({ length: round }, (_, index) => <option key={index + 1} value={index + 1}>Round {index + 1}</option>)}</select><div className="mt-6 space-y-3">{selectedRaceResults.slice(0, 3).map((row) => <div key={row.result_key} className="rounded-xl bg-[#13243a] p-4"><p className="font-bold">P{row.finishing_position} · {row.driver_name}</p><p className="text-sm text-[#a8b5c7]">{row.race_name} · {row.points} points · {row.positions_gained || 0} places gained</p></div>)}</div></article><article className="overflow-hidden rounded-2xl border border-[#22354f] bg-[#0e1b2d]"><div className="border-b border-[#22354f] px-5 py-4"><h3 className="font-bold">Round {selectedRaceRound} results</h3></div><SimpleTable rows={selectedRaceResults.slice(0, 12)} columns={[{ key: "finishing_position", label: "Finish" }, { key: "driver_name", label: "Driver" }, { key: "constructor_name", label: "Constructor" }, { key: "grid_position", label: "Grid" }, { key: "positions_gained", label: "Gained" }, { key: "points", label: "Points" }]} /></article></section>}
        {view === "constructors" && <section className="grid gap-6 xl:grid-cols-[1.3fr_.7fr]"><article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><div className="flex flex-wrap items-center justify-between gap-4"><div><h2 className="text-xl font-black">Constructor detail</h2><p className="text-sm text-[#a8b5c7]">Season-long championship points progression.</p></div><select value={selectedConstructor?.constructor_id ?? ""} onChange={(event) => setSelectedConstructorId(event.target.value)} className="rounded-lg border border-[#36516f] bg-[#07111f] px-3 py-2 text-sm font-bold text-white">{latestConstructors.map((row) => <option key={row.constructor_id} value={row.constructor_id}>{row.constructor_name}</option>)}</select></div><div className="mt-6 h-80"><ResponsiveContainer width="100%" height="100%"><AreaChart data={constructorTrend}><defs><linearGradient id="teamPoints" x1="0" x2="0" y1="0" y2="1"><stop offset="5%" stopColor="#35c2ff" stopOpacity={0.6}/><stop offset="95%" stopColor="#35c2ff" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#22354f" vertical={false}/><XAxis dataKey="round" stroke="#a8b5c7" tickLine={false} axisLine={false}/><YAxis stroke="#a8b5c7" tickLine={false} axisLine={false}/><Tooltip contentStyle={{ background: "#07111f", border: "1px solid #36516f", borderRadius: 12 }}/><Area type="monotone" dataKey="points" stroke="#35c2ff" fill="url(#teamPoints)" strokeWidth={3}/></AreaChart></ResponsiveContainer></div></article><article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><h3 className="font-bold">Current constructor standings</h3><p className="mb-4 text-sm text-[#a8b5c7]">Select a constructor to inspect its points curve.</p><SimpleTable rows={latestConstructors.slice(0, 10)} columns={[{ key: "championship_position", label: "Rank" }, { key: "constructor_name", label: "Constructor" }, { key: "championship_points", label: "Points" }]} /></article></section>}
        {view === "circuits" && <section className="grid gap-6 xl:grid-cols-[.8fr_1.2fr]"><article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><h2 className="text-xl font-black">Circuit trends</h2><p className="mb-5 text-sm text-[#a8b5c7]">Points and average finish for a selected driver at each circuit.</p><select value={selectedDriver?.driver_id ?? ""} onChange={(event) => setSelectedDriverId(event.target.value)} className="w-full rounded-lg border border-[#36516f] bg-[#07111f] px-3 py-2 text-sm font-bold text-white">{latestDrivers.map((row) => <option key={row.driver_id} value={row.driver_id}>{row.driver_name}</option>)}</select><div className="mt-6 h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={driverCircuitRows.slice(0, 10)} layout="vertical" margin={{ left: 36 }}><CartesianGrid stroke="#22354f" horizontal={false}/><XAxis type="number" stroke="#a8b5c7" tickLine={false} axisLine={false}/><YAxis dataKey="circuit_name" type="category" width={150} stroke="#a8b5c7" tickLine={false} axisLine={false}/><Tooltip contentStyle={{ background: "#07111f", border: "1px solid #36516f", borderRadius: 12 }}/><Bar dataKey="points" fill="#44d7a8" radius={[0, 5, 5, 0]}/></BarChart></ResponsiveContainer></div></article><article className="overflow-hidden rounded-2xl border border-[#22354f] bg-[#0e1b2d]"><div className="border-b border-[#22354f] px-5 py-4"><h3 className="font-bold">{selectedDriver?.driver_name ?? "Driver"} by circuit</h3></div><SimpleTable rows={driverCircuitRows} columns={[{ key: "circuit_name", label: "Circuit" }, { key: "races", label: "Races" }, { key: "average_finish", label: "Avg. finish" }, { key: "points", label: "Points" }]} /></article></section>}
        {view === "history" && <section className="grid gap-6 xl:grid-cols-[.8fr_1.2fr]"><article className="rounded-2xl border border-[#22354f] bg-[#0e1b2d] p-5"><h2 className="text-xl font-black">Historical season comparison</h2><p className="mb-5 text-sm text-[#a8b5c7]">Compare completed or in-progress seasons from the approved extract.</p><div className="grid grid-cols-2 gap-3"><select value={seasonA} onChange={(event) => setHistoricalSeasonA(event.target.value)} className="rounded-lg border border-[#36516f] bg-[#07111f] px-3 py-2 text-sm font-bold text-white">{seasons.map((value) => <option key={value}>{value}</option>)}</select><select value={seasonB} onChange={(event) => setHistoricalSeasonB(event.target.value)} className="rounded-lg border border-[#36516f] bg-[#07111f] px-3 py-2 text-sm font-bold text-white">{seasons.map((value) => <option key={value}>{value}</option>)}</select></div><div className="mt-6 h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={historicalRows}><CartesianGrid stroke="#22354f" vertical={false}/><XAxis dataKey="season" stroke="#a8b5c7" tickLine={false} axisLine={false}/><YAxis stroke="#a8b5c7" tickLine={false} axisLine={false}/><Tooltip contentStyle={{ background: "#07111f", border: "1px solid #36516f", borderRadius: 12 }}/><Bar dataKey="points" fill="#b68cff" radius={[5, 5, 0, 0]}/></BarChart></ResponsiveContainer></div></article><article className="overflow-hidden rounded-2xl border border-[#22354f] bg-[#0e1b2d]"><div className="border-b border-[#22354f] px-5 py-4"><h3 className="font-bold">Season summary</h3></div><SimpleTable rows={historicalRows} columns={[{ key: "season", label: "Season" }, { key: "races", label: "Races" }, { key: "points", label: "Points awarded" }, { key: "winner", label: "Most wins" }, { key: "wins", label: "Wins" }]} /></article></section>}
      </>}
    </section>
    <footer className="mx-auto max-w-7xl px-5 pb-8 text-xs text-[#71829a] md:px-10">Source: Jolpica F1 API · transformed in Snowflake/dbt · dashboard extracts generated with the least-privilege F1_BI_READER role.</footer>
  </main>;
}
