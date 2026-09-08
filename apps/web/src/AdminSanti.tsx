import { useState } from "react";
import { ShieldCheck, Palette, Activity, Bot } from "lucide-react";

export function AdminSanti() {
  const [activeTab, setActiveTab] = useState("logs");
  return (
    <section className="panel admin-panel">
      <div className="panel-head">
        <h2><ShieldCheck size={18}/> Panel de Administración - Santi</h2>
        <span className="badge">SUPERADMIN</span>
      </div>
      <p className="muted">Supabase Edge Functions configuradas para seguridad de APIs y Fine-Tuning. Monitoreo Vercel activo.</p>
      
      <div className="admin-tabs">
        <button className={activeTab === 'logs' ? 'active' : ''} onClick={() => setActiveTab('logs')}><Activity size={14}/> Logs de Acceso</button>
        <button className={activeTab === 'colors' ? 'active' : ''} onClick={() => setActiveTab('colors')}><Palette size={14}/> Configuración UI</button>
        <button className={activeTab === 'ai' ? 'active' : ''} onClick={() => setActiveTab('ai')}><Bot size={14}/> NotebookLM AI</button>
      </div>

      <div className="admin-content">
        {activeTab === 'logs' && (
          <div>
            <h3>Accesos Recientes</h3>
            <pre>
[2026-09-08 17:50] User: demo@ssscanner.com - Action: Login
[2026-09-08 17:55] User: santi - Action: Configuración modificada
[2026-09-08 18:02] API: Supabase RAG Endpoint Hit (Success)
            </pre>
          </div>
        )}
        {activeTab === 'colors' && (
          <div className="colors-config">
            <h3>Configuración de Tema</h3>
            <label>Color Principal <input type="color" defaultValue="#6ae9c1" /></label>
            <label>Fondo <input type="color" defaultValue="#0b1217" /></label>
            <button className="primary-button" style={{marginTop: '1rem'}}>Guardar Configuración</button>
          </div>
        )}
        {activeTab === 'ai' && (
          <div className="ai-config">
            <h3>Asistente de Mejoras (Brain NotebookLM)</h3>
            <p>Conectado a la base de conocimiento RAG MCP.</p>
            <textarea placeholder="Pregúntale a la IA sobre sugerencias de arquitectura..." rows={4} style={{width: '100%'}}></textarea>
            <button className="primary-button" style={{marginTop: '1rem'}}>Generar Ideas</button>
          </div>
        )}
      </div>
    </section>
  );
}
