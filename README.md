📧 Lirou Analytics - Classificador de Emails
Classificação inteligente de emails com IA para identificar mensagens produtivas vs improdutivas.

🚀 Como Executar
Backend (FastAPI)
bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
Disponível em: http://localhost:8001

Frontend (Vercel)
bash
cd frontend
python -m http.server 3000
Disponível em: http://localhost:3000

🌐 Deploy
Frontend (Vercel)
Conecte o repositório no Vercel

Deploy automático a cada push

Backend (VPS)
bash
uvicorn main:app --host 0.0.0.0 --port 8001
📁 Estrutura
text
lirou-analytics/
├── frontend/           # Interface web (HTML/CSS/JS)
├── backend/           # API FastAPI + ML
└── README.md
⚙️ Configuração DNS
text
A       @       76.76.21.21          (Vercel)
CNAME   www     cname.vercel-dns.com (Vercel)  
A       api     SEU_IP_VPS           (Backend)
🎯 Funcionalidades
✅ Classificação automática de emails

✅ Upload de arquivos (.txt, .pdf)

✅ Respostas sugeridas por IA

✅ Interface responsiva

✅ Métricas em tempo real

Acesse: https://lirouanalytics.site

Desenvolvido com FastAPI + JavaScript + Vercel