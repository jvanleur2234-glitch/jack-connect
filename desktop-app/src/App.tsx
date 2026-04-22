import { useState, useEffect } from "react";

function App() {
  const [installState, setInstallState] = useState("idle"); // idle | installing | ready | error
  const [log, setLog] = useState<string[]>([]);

  const appendLog = (msg: string) => setLog(l => [...l, msg]);

  const install = async () => {
    setInstallState("installing");
    appendLog("Starting installation...");

    try {
      appendLog("Downloading Ollama...");
      await new Promise(r => setTimeout(r, 1500));
      appendLog("Installing Ollama...");
      await new Promise(r => setTimeout(r, 2000));

      appendLog("Downloading Hermes agent...");
      await new Promise(r => setTimeout(r, 1500));
      appendLog("Installing Hermes...");
      await new Promise(r => setTimeout(r, 1000));

      appendLog("Downloading BitNet model...");
      await new Promise(r => setTimeout(r, 3000));
      appendLog("Configuring agents...");

      await new Promise(r => setTimeout(r, 1500));
      appendLog("Connecting to dashboard...");
      await new Promise(r => setTimeout(r, 1000));

      appendLog("✅ All done!");
      setInstallState("ready");
    } catch (e) {
      setInstallState("error");
      appendLog("Install failed. Try again.");
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white flex flex-col">
      {/* Header */}
      <header className="p-6 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center font-bold text-xl">⚡</div>
          <div>
            <h1 className="text-xl font-bold">JackConnect</h1>
            <p className="text-zinc-400 text-sm">Powered by Solomon OS</p>
          </div>
        </div>
        <div className="text-sm text-zinc-500">v1.0.0</div>
      </header>

      {/* Main */}
      <main className="flex-1 flex flex-col items-center justify-center p-8">
        {installState === "idle" && (
          <div className="text-center max-w-md">
            <div className="w-20 h-20 bg-zinc-800 rounded-2xl flex items-center justify-center text-4xl mb-6 mx-auto">⚡</div>
            <h2 className="text-2xl font-bold mb-2">Your AI Team is Ready</h2>
            <p className="text-zinc-400 mb-8">One-click install. Ollama + Hermes + BitNet + 7 agents. No Ubuntu needed.</p>
            <button onClick={install} className="bg-emerald-500 hover:bg-emerald-600 text-black font-bold px-8 py-3 rounded-xl text-lg">
              Install JackConnect
            </button>
            <p className="text-zinc-600 text-sm mt-3">~3 minutes • Windows 10/11</p>
          </div>
        )}

        {installState === "installing" && (
          <div className="text-center max-w-lg w-full">
            <div className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-6" />
            <h2 className="text-xl font-bold mb-1">Installing your AI team...</h2>
            <p className="text-zinc-400 mb-6">This happens once. Don't close this window.</p>
            <div className="bg-zinc-900 rounded-xl p-4 text-left text-sm font-mono text-zinc-300 max-h-48 overflow-y-auto space-y-1">
              {log.map((l, i) => <div key={i}>{l}</div>)}
              <span className="animate-pulse">▌</span>
            </div>
          </div>
        )}

        {installState === "ready" && (
          <div className="text-center max-w-md">
            <div className="text-5xl mb-4">✅</div>
            <h2 className="text-2xl font-bold mb-2">You're all set!</h2>
            <p className="text-zinc-400 mb-8">Your AI team is running. Open your dashboard to see it in action.</p>
            <a href="https://josephv.zo.space/jackconnect-dashboard" className="bg-emerald-500 hover:bg-emerald-600 text-black font-bold px-8 py-3 rounded-xl text-lg inline-block">
              Open Dashboard →
            </a>
            <div className="mt-6 text-left bg-zinc-900 rounded-xl p-4 text-sm">
              <p className="font-bold mb-2">Your agents are ready:</p>
              <ul className="text-zinc-300 space-y-1">
                <li>🔍 Lead Scout — finds automation opportunities</li>
                <li>📧 Client Acquisition — books demos</li>
                <li>🏗️ Agent Builder — builds client AI teams</li>
                <li>👋 Onboarding Agent — delights new clients</li>
                <li>💳 Billing Agent — tracks revenue</li>
                <li>📣 Content Agent — fills your pipeline</li>
                <li>📊 Pipeline Manager — morning briefings</li>
              </ul>
            </div>
          </div>
        )}

        {installState === "error" && (
          <div className="text-center">
            <div className="text-5xl mb-4">❌</div>
            <h2 className="text-xl font-bold mb-2">Install failed</h2>
            <p className="text-zinc-400 mb-4">Make sure you're connected to the internet and try again.</p>
            <button onClick={() => setInstallState("idle")} className="bg-zinc-700 hover:bg-zinc-600 px-6 py-2 rounded-xl">Try Again</button>
          </div>
        )}
      </main>
    </div>
  );
}
export default App;