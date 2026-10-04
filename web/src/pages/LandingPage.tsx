import { ArrowRight, ArrowUpRight, Check, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import Brand from "../components/Brand";

const steps = [
  {
    number: "01",
    title: "Start a trip",
    copy: "Bring your people and plans into one shared space.",
  },
  {
    number: "02",
    title: "Drop in expenses",
    copy: "Add a cost once. Pick who was there and how to split it.",
  },
  {
    number: "03",
    title: "Settle up simply",
    copy: "Clear balances show who pays whom, with fewer transfers.",
  },
];

export default function LandingPage() {
  return (
    <div className="landing-page">
      <header className="landing-header">
        <Brand />
        <nav aria-label="Main navigation" className="landing-nav">
          <a href="#how-it-works">How it works</a>
          <a href="#why-contridedo">Why contriDedo</a>
        </nav>
        <Link className="header-cta" to="/dashboard">
          Open your trips <ArrowUpRight size={16} strokeWidth={2.2} />
        </Link>
      </header>

      <main>
        <section className="landing-hero">
          <div className="hero-copy">
            <div className="eyebrow"><Sparkles size={14} /> Good trips, clear tabs</div>
            <h1>Make the trip.<br /><span>Not the spreadsheet.</span></h1>
            <p className="hero-description">
              Keep every shared cost in one clear ledger, settle up with fewer
              transfers, and get back to the people you came with.
            </p>
            <div className="hero-actions">
              <Link className="button button-primary" to="/dashboard">
                Start a trip <ArrowRight size={17} />
              </Link>
              <a className="text-link" href="#how-it-works">See how it works</a>
            </div>
            <div className="hero-proof">
              <div aria-hidden="true" className="proof-avatars">
                <span>J</span><span>M</span><span>A</span><span>+</span>
              </div>
              <p><strong>Better together.</strong><br />Every traveler, in the loop.</p>
            </div>
          </div>

          <div className="hero-visual">
            <img
              alt="A mountain lake surrounded by green hills, ready for a weekend away"
              className="hero-photo"
              src="https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=1500&q=85"
            />
            <div className="photo-label">
              <span className="photo-label-icon"><Check size={16} /></span>
              <span><strong>Everyone's in the loop</strong><small>One shared trip, no awkward asks</small></span>
            </div>
            <div className="photo-index">A little less tab-keeping</div>
          </div>
        </section>

        <section className="landing-strip" aria-label="Product benefits">
          <p>Trips are for being there.</p>
          <span><Check size={15} /> Every cost in one place</span>
          <span><Check size={15} /> Splits that add up</span>
          <span><Check size={15} /> Clear ways to settle</span>
        </section>

        <section className="how-section" id="how-it-works">
          <div className="section-heading">
            <div>
              <div className="eyebrow">The trip, minus the tallying</div>
              <h2>Good plans. Clear numbers.</h2>
            </div>
            <p>From the first booking to the last coffee, everyone knows where they stand.</p>
          </div>
          <div className="steps-grid">
            {steps.map((step) => (
              <article className="step-item" key={step.number}>
                <span className="step-number">{step.number}</span>
                <h3>{step.title}</h3>
                <p>{step.copy}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-bottom" id="why-contridedo">
          <div>
            <div className="eyebrow">The best part is the trip</div>
            <h2>Less “who owes what?”<br />More “remember when?”</h2>
          </div>
          <Link className="button button-dark" to="/dashboard">
            Take a look around <ArrowRight size={17} />
          </Link>
        </section>
      </main>
      <footer className="landing-footer">
        <Brand />
        <p>Made for the people you go places with.</p>
        <span>© 2026 contriDedo</span>
      </footer>
    </div>
  );
}
