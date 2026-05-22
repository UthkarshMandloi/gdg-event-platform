"use client"; // Tells Next.js this is a client-side component

import React, { useEffect, useState } from "react";
import Link from "next/link";
// @ts-expect-error - Next.js build fails because Babel standalone lacks official TS types
import * as Babel from '@babel/standalone';

// The Barrier Breaker: Dynamic Runtime React Compiler
function DynamicReactCompiler({ code, eventData, speakersData }: { code: string, eventData: any, speakersData: any }) {
  const [Component, setComponent] = useState<React.ElementType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      // 1. Transpile JSX/TSX into plain JS using Babel in the browser
      const transpiled = Babel.transform(code, {
        presets: ['env', 'react', 'typescript'],
        filename: 'custom.tsx'
      }).code;

      // 2. Create a secure CommonJS-like module environment
      const module = { exports: {} as any };
      const requireFunc = (moduleName: string) => {
        if (moduleName === 'react') return React;
        throw new Error(`Cannot require '${moduleName}' in runtime compiler.`);
      };

      // 3. Execute the transpiled string with our scoped variables
      const evaluate = new Function('React', 'require', 'module', 'exports', transpiled || '');
      evaluate(React, requireFunc, module, module.exports);

      // Extract the component (either default export or main export)
      const ExportedComponent = module.exports.default || module.exports;

      if (typeof ExportedComponent !== 'function') {
        throw new Error('The code did not export a valid React functional component. Make sure to "export default function MyComponent() {...}"');
      }

      setComponent(() => ExportedComponent);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message);
      setComponent(null);
    }
  }, [code]);

  if (error) {
    return <div className="p-8 bg-red-50 text-red-700 border-2 border-red-500 rounded-xl m-10 font-mono text-sm"><h1>Runtime Compiler Error:</h1><pre className="mt-4 whitespace-pre-wrap">{error}</pre></div>;
  }

  if (!Component) return <div className="p-10 text-center font-mono">Compiling Custom React Overrides...</div>;

  // Render the compiled component! We pass the event data to it in case the custom code wants to use it.
  return <Component event={eventData} speakers={speakersData} />;
}

// Define the shape of our data
interface EventData {
  title: string;
  date: string;
  venue: string;
  is_test_active: boolean;
  test_link: string | null;
}

interface Speaker {
  name: string;
  bio: string;
}

export default function Home() {
  const [event, setEvent] = useState<EventData | null>(null);
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch data from our Django backend!
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/event/`)
      .then((res) => res.json())
      .then((data) => {
        setEvent(data.event);
        setSpeakers(data.speakers);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching event data:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-xl">Loading event details...</div>;
  }

  // --- THE BARRIER BREAKER ---
  // If the backend has custom theme code, and it contains "export default", it is a React component!
  const customCode = event?.custom_theme_code || '';
  if (customCode.includes('export default')) {
    return <DynamicReactCompiler code={customCode} eventData={event} speakersData={speakers} />;
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      {/* Hero Section */}
      <section className="bg-blue-600 text-white py-20 px-6 text-center">
        <h1 className="text-5xl font-bold mb-4">{event?.title || "Upcoming Tech Event"}</h1>
        <p className="text-xl mb-8 opacity-90">Join us for a day of learning, networking, and innovation.</p>
        
        <div className="flex justify-center gap-4 mb-8">
          <div className="bg-blue-700 px-6 py-3 rounded-lg">
            <p className="font-semibold text-sm text-blue-200">Date</p>
            <p className="text-lg">{event ? new Date(event.date).toLocaleDateString() : "TBA"}</p>
          </div>
          <div className="bg-blue-700 px-6 py-3 rounded-lg">
            <p className="font-semibold text-sm text-blue-200">Venue</p>
            <p className="text-lg">{event?.venue || "TBA"}</p>
          </div>
        </div>

        <Link 
          href="/login" 
          className="bg-white text-blue-600 font-bold py-3 px-8 rounded-full hover:bg-slate-100 transition shadow-lg"
        >
          Login with College ID to Register
        </Link>
      </section>

      {/* Dynamic Speakers Section */}
      <section className="py-20 px-6 max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12">Meet Our Speakers</h2>
        
        {speakers.length === 0 ? (
          <p className="text-center text-slate-500 italic">Speakers will be revealed soon. Stay tuned!</p>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {speakers.map((speaker, index) => (
              <div key={index} className="bg-white p-6 rounded-xl shadow-md border border-slate-100">
                <div className="w-16 h-16 bg-blue-100 rounded-full mb-4 flex items-center justify-center text-blue-600 font-bold text-xl">
                  {speaker.name.charAt(0)}
                </div>
                <h3 className="text-xl font-bold mb-2">{speaker.name}</h3>
                <p className="text-slate-600 text-sm leading-relaxed">{speaker.bio}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}