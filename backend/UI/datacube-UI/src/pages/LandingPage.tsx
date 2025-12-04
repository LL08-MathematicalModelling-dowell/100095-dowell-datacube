import { format } from "date-fns";
import { motion } from "framer-motion";
import { ArrowRight, Check, Github, Mail, Menu, Rocket, Shield, Star, X, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

// const testimonials = [
//   { name: "Alex Chen", role: "CTO @ Stealth Startup", text: "DataCube saved us 3 months of infra work. We shipped in 2 weeks.", avatar: "AC" },
//   { name: "Sarah Kim", role: "Full-Stack @ Fintech", text: "Best dev experience I've had with a database. Period.", avatar: "SK" },
//   { name: "Marcus Johnson", role: "Indie Hacker", text: "From zero to 10k users in a weekend. Thank you DataCube.", avatar: "MJ" },
// ];

const blogPosts = [
  { title: "Why We Built DataCube", date: "2025-03-20", excerpt: "The story behind replacing MongoDB Atlas with something simpler.", readTime: "4 min" },
  { title: "JWT vs API Keys: Which Should You Use?", date: "2025-03-15", excerpt: "A deep dive into authentication patterns for modern backends.", readTime: "6 min" },
  { title: "Scaling to 1M Requests with Zero Ops", date: "2025-03-10", excerpt: "How DataCube handles traffic spikes without you lifting a finger.", readTime: "5 min" },
];

const PricingTier = ({ title, price, yearlyPrice, features, popular, cta }: any) => (
  <motion.div
    whileHover={{ y: -12, scale: 1.02 }}
    className={`relative p-10 rounded-3xl border-2 transition-all ${
      popular
        ? "border-[var(--green-dark)] bg-gradient-to-b from-[var(--green-dark)]/10 to-transparent shadow-2xl shadow-[var(--green-dark)]/30"
        : "border-[var(--border-color)] bg-[var(--bg-dark-2)]"
    }`}
  >
    {popular && (
      <div className="absolute -top-5 left-1/2 -translate-x-1/2 bg-[var(--green-dark)] text-white px-6 py-2 rounded-full text-sm font-bold flex items-center gap-2">
        <Star className="w-4 h-4 fill-current" />
        Most Popular
      </div>
    )}
    <h3 className="text-3xl font-bold text-[var(--green-dark)] mb-4">{title}</h3>
    <div className="mb-8">
      <span className="text-6xl font-bold text-[var(--text-light)]">${price}</span>
      <span className="text-[var(--text-muted)] text-xl">/month</span>
      {yearlyPrice && <span className="block text-sm text-[var(--text-muted)] mt-2">or ${yearlyPrice}/year (Save 20%)</span>}
    </div>
    <ul className="space-y-4 mb-10">
      {features.map((f: string) => (
        <li key={f} className="flex items-start gap-3">
          <Check className="w-6 h-6 text-[var(--green-dark)] flex-shrink-0 mt-0.5" />
          <span className="text-lg">{f}</span>
        </li>
      ))}
    </ul>
    <Link
      to={cta.to}
      className={`block text-center py-4 rounded-xl font-bold text-xl transition-all ${
        popular
          ? "bg-[var(--green-dark)] text-white hover:bg-[var(--green-dark)]/90 shadow-lg"
          : "bg-[var(--bg-dark-3)] hover:bg-[var(--bg-dark-3)]/80"
      }`}
    >
      {cta.text}
    </Link>
  </motion.div>
);

const LandingPage = () => {
  // const [isDark, setIsDark] = useState(true);
  // const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const [visitors, setVisitors] = useState(12487);
  const githubStars = 2847;
  // const [githubStars, setGithubStars] = useState(2847);
  const [email, setEmail] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // useEffect(() => {
  //   const interval = setInterval(() => {
  //     setCurrentTestimonial((i) => (i + 1) % testimonials.length);
  //   }, 6000);
  //   return () => clearInterval(interval);
  // }, []);

  // Simulate live visitors
  useEffect(() => {
    const interval = setInterval(() => {
      setVisitors(v => v + Math.floor(Math.random() * 3));
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  // Fetch real GitHub stars (replace with your repo)
  // useEffect(() => {
  //   fetch("https://api.github.com/repos/username/datacube")
  //     .then(r => r.json())
  //     .then(d => setGithubStars(d.stargazers_count || 2847))
  //     .catch(() => {});
  // }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[var(--bg-dark-1)] via-[var(--bg-dark-2)] to-[var(--bg-dark-1)] text-[var(--text-light)]  overflow-x-hidden">
      {/* Dark Mode Toggle */}
      {/* <button
        onClick={() => setIsDark(!isDark)}
        className="fixed top-14 right-6 z-50 p-3 rounded-full bg-[var(--bg-dark-3)] border border-[var(--border-color)] hover:border-[var(--green-dark)] transition-all"
        aria-label="Toggle dark mode"
      >
        {isDark ? <Sun className="w-6 h-6" /> : <Moon className="w-6 h-6" />}
      </button> */}

      {/* Mobile Menu Button */}
      {/* <button
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        className="fixed top-6 left-6 z-50 p-3 rounded-full bg-[var(--bg-dark-3)] border border-[var(--border-color)] lg:hidden"
      >
        {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button> */}

      {/* Hero */}
      <section className="relative pt-40 pb-32 px-6 text-center overflow-hidden">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1 }}
          className="max-w-6xl mx-auto"
        >
          <h1 className="text-7xl sm:text-9xl font-black text-transparent bg-clip-text bg-gradient-to-r from-[var(--green-dark)] via-emerald-400 to-[var(--green-dark)] mb-6 leading-tight">
            DataCube
          </h1>
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-3xl sm:text-5xl font-light text-[var(--text-muted)] mb-8"
          >
            The Database That Ships With You
          </motion.p>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="text-xl sm:text-2xl mb-12 max-w-4xl mx-auto leading-relaxed text-[var(--text-light)]/80"
          >
            No servers. No YAML. No tears. Just JSON in, JSON out — with JWT, API keys, and zero ops.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="flex flex-col sm:flex-row gap-8 justify-center items-center mb-16"
          >
            <Link
              to="/register"
              className="group inline-flex items-center gap-4 bg-[var(--green-dark)] hover:bg-[var(--green-dark)]/90 text-white px-12 py-6 rounded-2xl text-2xl font-bold transition-all duration-300 transform hover:scale-110 shadow-2xl"
            >
              Start Free Instantly
              <Rocket className="w-8 h-8 group-hover:translate-x-2 transition-transform" />
            </Link>
            <Link
              to="/api-docs"
              className="inline-flex items-center gap-4 border-2 border-[var(--green-dark)] text-[var(--green-dark)] hover:bg-[var(--green-dark)]/10 px-12 py-6 rounded-2xl text-2xl font-bold transition-all duration-300"
            >
              <Zap className="w-8 h-8" />
              API Docs
            </Link>
          </motion.div>

          {/* Live Stats */}
          <div className="flex flex-wrap justify-center gap-12 text-center">
            <div>
              <div className="text-4xl font-bold text-[var(--green-dark)]">{visitors.toLocaleString()}+</div>
              <div className="text-[var(--text-muted)]">Developers Online Now</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-[var(--green-dark)] flex items-center gap-2 justify-center">
                <Github className="w-8 h-8" />
                {githubStars.toLocaleString()}
              </div>
              <div className="text-[var(--text-muted)]">GitHub Stars</div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="py-32 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-12">
          {[
            { icon: Rocket, title: "Zero Ops", desc: "No servers, no scaling worries. Just code." },
            { icon: Shield, title: "Secure by Default", desc: "JWT + API Keys. You own your data." },
            { icon: Zap, title: "Instant API", desc: "Full CRUD in seconds. No boilerplate." },
          ].map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.2 }}
              className="text-center group"
            >
              <div className="inline-block p-8 rounded-full bg-[var(--green-dark)]/10 mb-8 group-hover:bg-[var(--green-dark)]/20 transition-all">
                <f.icon className="w-20 h-20 text-[var(--green-dark)]" />
              </div>
              <h3 className="text-3xl font-bold mb-4">{f.title}</h3>
              <p className="text-xl text-[var(--text-muted)]">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="py-32 px-6 bg-[var(--bg-dark-2)]/30">
        <div className="text-center mb-20">
          <h2 className="text-6xl font-bold mb-6">Pricing That Makes Sense</h2>
          <p className="text-2xl text-[var(--text-muted)]">One plan. Unlimited everything.</p>
        </div>
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12">
          <PricingTier
            title="Free Forever"
            price="0"
            features={[
              "10,000 API calls/month",
              "1 database",
              "Full API access",
              "Community support",
            ]}
            cta={{ text: "Start Free", to: "/register" }}
          />
          <PricingTier
            title="Pro"
            price="29"
            yearlyPrice="278"
            popular
            features={[
              "Unlimited API calls",
              "Unlimited databases",
              "Priority support",
              "Team collaboration",
              "Advanced analytics",
              "99.99% uptime SLA",
              "Custom domains",
            ]}
            cta={{ text: "Go Pro →", to: "/register" }}
          />
        </div>
      </section>

      {/* Blog Preview */}
      <section className="py-32 px-6">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold mb-4">From Our Blog</h2>
          <Link to="/blog" className="text-[var(--green-dark)] hover:underline text-xl">Read all posts →</Link>
        </div>
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-10">
          {blogPosts.map((post, i) => (
            <motion.article
              key={i}
              whileHover={{ y: -8 }}
              className="bg-[var(--bg-dark-2)] rounded-2xl p-8 border border-[var(--border-color)] hover:border-[var(--green-dark)]/50 transition-all"
            >
              <time className="text-sm text-[var(--text-muted)]">
                {format(new Date(post.date), "MMM d, yyyy")} · {post.readTime}
              </time>
              <h3 className="text-2xl font-bold mt-4 mb-3 text-[var(--green-dark)]">
                {post.title}
              </h3>
              <p className="text-[var(--text-muted)] leading-relaxed">
                {post.excerpt}
              </p>
              <Link to="/blog" className="inline-flex items-center gap-2 text-[var(--green-dark)] mt-6 hover:gap-4 transition-all">
                Read more <ArrowRight className="w-5 h-5" />
              </Link>
            </motion.article>
          ))}
        </div>
      </section>

      {/* Waitlist / Early Access */}
      <section className="py-32 px-6 bg-gradient-to-r from-[var(--green-dark)]/20 to-transparent">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-6xl font-bold mb-8">Be the First to Know</h2>
          <p className="text-2xl mb-12 text-[var(--text-light)]/80">
            Join 10,000+ developers waiting for the next big thing.
          </p>
          <form className="flex flex-col sm:flex-row gap-6 max-w-2xl mx-auto">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="flex-1 px-8 py-6 rounded-xl bg-[var(--bg-dark-2)] border border-[var(--border-color)] focus:border-[var(--green-dark)] focus:outline-none text-xl"
            />
            <button
              type="submit"
              className="bg-[var(--green-dark)] hover:bg-[var(--green-dark)]/90 text-white px-12 py-6 rounded-xl text-xl font-bold transition-all transform hover:scale-105 shadow-xl flex items-center justify-center gap-3"
            >
              <Mail className="w-6 h-6" />
              Join Waitlist
            </button>
          </form>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-32 px-6 text-center">
        <h2 className="text-7xl font-black mb-8 bg-clip-text text-transparent bg-gradient-to-r from-[var(--green-dark)] to-emerald-400">
          Stop Waiting. Start Building.
        </h2>
        <Link
          to="/register"
          className="inline-flex items-center gap-6 bg-[var(--green-dark)] hover:bg-[var(--green-dark)]/90 text-white px-16 py-8 rounded-2xl text-3xl font-bold transition-all duration-300 transform hover:scale-110 shadow-3xl"
        >
          Launch Your App Today
          <Rocket className="w-12 h-12" />
        </Link>
      </section>

      <footer className="py-16 text-center border-t border-[var(--border-color)] text-[var(--text-muted)]">
        <p className="mb-4">© 2025 DataCube • Built for developers who ship</p>
        <div className="flex justify-center gap-8 text-sm">
          <Link to="/privacy" className="hover:text-[var(--green-dark)]">Privacy</Link>
          <Link to="/terms" className="hover:text-[var(--green-dark)]">Terms</Link>
          <Link to="/status" className="hover:text-[var(--green-dark)]">Status</Link>
          {/* <a href="https://github.com/username/datacube" className="hover:text-[var(--green-dark)] flex items-center gap-2">
            <Github className="w-5 h-5" /> GitHub
          </a> */}
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;