"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

function applyTheme(code: string) {
  if (!code) return null;
  try {
    const theme = JSON.parse(code);
    return `
      main { background-color: ${theme.colors?.background} !important; color: ${theme.colors?.textMain} !important; font-family: ${theme.fonts?.body || 'inherit'} !important; border-radius: ${theme.borderRadius || '0'} !important; }
      h1, h2, h3, h4, h5, h6 { color: ${theme.colors?.primary} !important; font-family: ${theme.fonts?.heading || 'inherit'} !important; }
      .bg-white { background-color: #1a1a1a !important; border-color: ${theme.colors?.secondary} !important; }
      .text-slate-500, .text-slate-600, .text-slate-700 { color: ${theme.colors?.textMuted} !important; }
      .bg-slate-50 { background-color: ${theme.colors?.background} !important; }
      nav h1 { color: ${theme.colors?.primary} !important; }
      button[type="submit"] { background-color: ${theme.colors?.primary} !important; color: #000 !important; }
      input, select, textarea { background-color: #222 !important; color: ${theme.colors?.textMain} !important; border-color: ${theme.colors?.textMuted} !important; }
      input:focus, select:focus, textarea:focus { border-color: ${theme.colors?.secondary} !important; }
    `;
  } catch(e) {
    // If it's not JSON, assume it's raw CSS
    return code;
  }
}

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  // State for Dynamic Answers
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [fileAnswers, setFileAnswers] = useState<Record<string, File>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetchDashboard = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push("/login"); return;
      }
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/dashboard/`, {
          headers: { "Authorization": `Token ${token}` }
        });
        if (!res.ok) throw new Error("Failed to fetch");
        const json = await res.json();
        setData(json);
      } catch (err) {
        localStorage.removeItem("token");
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, [router]);

  const handleAnswerChange = (label: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [label]: value }));
  };

  const handleFileChange = (label: string, file: File) => {
    setFileAnswers((prev) => ({ ...prev, [label]: file }));
  };

  const handleRegistrationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const token = localStorage.getItem("token");

    const formData = new FormData();
    // Add text/dropdown answers as JSON
    formData.append("answers", JSON.stringify(answers));
    
    // Append all selected files dynamically
    Object.entries(fileAnswers).forEach(([label, file]) => {
      formData.append(`file_${label}`, file);
    });

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/dashboard/`, {
        method: "POST",
        headers: { "Authorization": `Token ${token}` },
        body: formData
      });
      if (res.ok) window.location.reload();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (loading) return <div className="min-h-screen flex justify-center items-center">Loading your dashboard...</div>;
  if (!data) return null;

  return (
    <>
      {data.event?.custom_theme_code && (
        <style dangerouslySetInnerHTML={{ __html: applyTheme(data.event.custom_theme_code) || '' }} />
      )}
      <main className="min-h-screen bg-slate-50 text-slate-900 pb-20">
        <nav className="bg-white shadow-sm px-6 py-4 flex justify-between items-center mb-8">
        <h1 className="font-bold text-xl text-blue-600">Student Portal</h1>
        <button onClick={handleLogout} className="text-slate-500 hover:text-red-500 transition font-medium">Logout</button>
      </nav>

      <div className="max-w-4xl mx-auto px-6">
        <header className="mb-10">
          <h2 className="text-3xl font-bold">Welcome, {data.user.first_name}!</h2>
          <p className="text-slate-500">{data.user.email}</p>
        </header>

        {!data.user.is_registered ? (
          <div className="bg-white p-8 rounded-2xl shadow-md border border-slate-100">
            <h3 className="text-2xl font-bold mb-4">Complete Your Registration</h3>
            <p className="text-slate-600 mb-8">Please fill out the following details to secure your spot.</p>
            
            <form onSubmit={handleRegistrationSubmit} className="space-y-6">
              
              {data.event?.form_fields?.map((field: any) => (
                <div key={field.id} className="flex flex-col">
                  <label className="text-sm font-semibold text-slate-700 mb-2">
                    {field.label} {field.is_required && <span className="text-red-500">*</span>}
                  </label>
                  
                  {field.field_type === 'text' && (
                    <input type="text" required={field.is_required} 
                      className="px-4 py-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none"
                      onChange={(e) => handleAnswerChange(field.label, e.target.value)} />
                  )}
                  
                  {field.field_type === 'textarea' && (
                    <textarea required={field.is_required} rows={3}
                      className="px-4 py-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none"
                      onChange={(e) => handleAnswerChange(field.label, e.target.value)} />
                  )}

                  {field.field_type === 'select' && (
                    <select required={field.is_required}
                      className="px-4 py-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                      onChange={(e) => handleAnswerChange(field.label, e.target.value)}>
                      <option value="">Select an option</option>
                      {field.options.split(',').map((opt: string) => (
                        <option key={opt.trim()} value={opt.trim()}>{opt.trim()}</option>
                      ))}
                    </select>
                  )}

                  {field.field_type === 'checkbox' && (
                    <div className="flex items-center gap-2">
                      <input type="checkbox" required={field.is_required} className="w-5 h-5"
                        onChange={(e) => handleAnswerChange(field.label, e.target.checked ? "Yes" : "No")} />
                      <span className="text-slate-600 text-sm">Yes</span>
                    </div>
                  )}

                  {/* NEW: Dynamic File Upload Input */}
                  {field.field_type === 'file' && (
                    <input type="file" required={field.is_required}
                      accept=".pdf,image/*"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          handleFileChange(field.label, e.target.files[0]);
                        }
                      }}
                      className="block w-full text-sm text-slate-500 file:mr-4 file:py-3 file:px-6 file:rounded-full file:border-0 file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 transition cursor-pointer"
                    />
                  )}
                </div>
              ))}

              <button type="submit" disabled={submitting}
                className="w-full bg-blue-600 text-white font-bold py-4 rounded-xl hover:bg-blue-700 transition shadow-md disabled:opacity-70 mt-8">
                {submitting ? "Uploading & Syncing..." : "Submit Registration"}
              </button>
            </form>
          </div>
       ) : (
          <div className="space-y-8">
            <div className="bg-white p-8 rounded-2xl shadow-md border border-slate-100">
              
              {data.user.registration_status === 'rejected' ? (
                <div className="bg-red-50 border border-red-200 text-red-800 p-6 rounded-xl text-center">
                  <h3 className="text-2xl font-bold mb-2">Registration Closed</h3>
                  <p>We are sorry, but we are currently at full capacity for this event. Keep an eye out for future events!</p>
                </div>
              ) : data.user.registration_status === 'pending' ? (
                <div className="bg-amber-50 border border-amber-200 text-amber-800 p-6 rounded-xl flex items-center gap-4">
                  <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
                  <div>
                    <h4 className="font-bold text-lg">Form Under Review</h4>
                    <p className="opacity-90">We have received your details! Our team is reviewing your application. You will receive your ticket soon.</p>
                  </div>
                </div>
              ) : (
                <>
                  <h3 className="text-2xl font-bold mb-4">Your E-Ticket</h3>
                  {data.user.ticket_url && (
                    <div className="flex flex-col md:flex-row gap-8 items-start">
                      <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 w-full md:w-1/2">
                        <img src={data.user.ticket_url} alt="Your Event Ticket" className="w-full h-auto rounded-lg shadow-sm" />
                      </div>
                      <div>
                        <h4 className="font-bold text-lg mb-2 text-green-600">✓ Ticket Generated</h4>
                        <p className="text-slate-600 mb-6">Your ticket has been sent to your email. You can also download it right here. Please keep the QR code handy at the venue!</p>
                        <a href={data.user.ticket_url} download target="_blank" className="bg-slate-900 text-white font-semibold py-2 px-6 rounded-lg hover:bg-slate-800 transition block text-center">Download Ticket</a>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
    </>
  );
}