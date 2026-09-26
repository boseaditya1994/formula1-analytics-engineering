"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
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

export default function Home() {
  const [races, setRaces] = useState<Row[]>([]);
  const [drivers, setDrivers] = useState<Row[]>([]);
  const [constructors, setConstructors] = useState<Row[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "empty">("loading");
  const [season, setSeason] = useState("");

  useEffect(() => {
    Promise.all([
      fetch("/data/driver_race_performance.csv").then((r) => r.ok ? r.text() : ""),
      fetch("/data/driver_championship_progression.csv").then((r) => r.ok ? r.text() : ""),
      fetch("/data/constructor_championship_progression.csv").then((r) => r.ok ? r.text() : ""),
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
      {status === "ready" && <><div className="mb-7 flex flex-wrap items-end justify-between gap-3"><div><p className="text-sm text-[#a8b5c7]">Season {season} · through round {round}</p><h2 className="mt-1 text-3xl font-black tracking-tight">At a glance</h2></div><p className="max-w-md text-right text-sm text-[#a8b5c7]">Data is a Snowflake MARTS snapshot, not live timing.</p></div>
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
        <div className="mt-6 grid gap-6 xl:grid-cols-2"><Standings title="Driver standings" rows={latestDrivers} name="driver_name" /><Standings title="Constructor standings" rows={latestConstructors} name="constructor_name" /></div>
      </>}
    </section>
    <footer className="mx-auto max-w-7xl px-5 pb-8 text-xs text-[#71829a] md:px-10">Source: Jolpica F1 API · transformed in Snowflake/dbt · dashboard extracts generated with the least-privilege F1_BI_READER role.</footer>
  </main>;
}
