import Link from "next/link";

export default function Home() {
  return (
    <main className="container">
      <section className="hero">
        <p className="muted">OPPORTUNITY RADAR / PERSONALIZED DISCOVERY</p>
        <h1>Find the opportunities that fit your next move.</h1>
        <p>Build a profile once. Get a sharper stream of internships, research, hackathons, and early-career paths matched to your goals.</p>
        <div className="hero-actions">
          <Link href="/login"><button>Login</button></Link>
          <Link href="/register"><button>Register</button></Link>
        </div>
      </section>
    </main>
  );
}
