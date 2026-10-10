"use client";

import { useState } from "react";
import {
  LandingPage,
  type EnterIntent,
} from "@/components/LandingPage";
import { RadarApp } from "@/components/RadarApp";

type Phase = "landing" | "app";

export default function Home() {
  const [phase, setPhase] = useState<Phase>("landing");
  const [intent, setIntent] = useState<EnterIntent>("map");
  const [visible, setVisible] = useState(true);

  function enter(next: EnterIntent) {
    setIntent(next);
    setVisible(false);
    window.setTimeout(() => {
      setPhase("app");
      setVisible(true);
    }, 280);
  }

  function goHome() {
    setVisible(false);
    window.setTimeout(() => {
      setPhase("landing");
      setVisible(true);
    }, 280);
  }

  return (
    <div
      className={`app-shell ${visible ? "app-shell--in" : "app-shell--out"}`}
    >
      {phase === "landing" ? (
        <LandingPage onEnter={enter} />
      ) : (
        <RadarApp
          key={intent}
          initialTab={intent}
          onHome={goHome}
        />
      )}
    </div>
  );
}
