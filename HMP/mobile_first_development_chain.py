
"""
Cadeia HMP para desenvolvimento mobile-first completo
Cria projetos web com PWA e suporte a Capacitor
"""

import os
import logging
from typing import Dict, Any

class MobileFirstDevelopmentChain:
    """Implementação da cadeia HMP para desenvolvimento mobile-first."""
    
    def __init__(self):
        self.logger = logging.getLogger('HMP.MobileFirstChain')
    
    def execute_mobile_first_pipeline(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a cadeia completa de desenvolvimento mobile-first.
        Todos os projetos são criados dentro da pasta ARTEFATOS.
        """
        
        # Configuração padrão
        config = {
            'project_name': project_config.get('project_name', 'mobilefirst-app'),
            'description': project_config.get('description', 'Aplicativo web mobile-first com PWA'),
            'author': project_config.get('author', 'Noka'),
            'features': project_config.get('features', ['auth', 'api', 'offline', 'push', 'ui-components']),
            'ui_lib': project_config.get('ui_lib', 'react'),
            'css_lib': project_config.get('css_lib', 'tailwind'),
            'target_envs': project_config.get('target_envs', ['web', 'pwa', 'android'])
        }
        
        # FASE 0: Preparação em ARTEFATOS
        artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ARTEFATOS")
        project_dir = os.path.join(artifacts_dir, config['project_name'])
        
        # Criar estrutura do projeto
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'src'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'public'), exist_ok=True)
        
        self.logger.info(f"🚀 Criando projeto mobile-first em: {project_dir}")
        
        # FASE 1: Arquivos principais
        self._create_main_files(project_dir, config)
        
        # FASE 2: PWA e offline support
        self._setup_pwa(project_dir, config)
        
        # FASE 3: Componentes UI responsivos
        self._create_ui_components(project_dir, config)
        
        # FASE 4: Scripts e configuração
        self._setup_build_scripts(project_dir, config)
        
        # FASE 5: Documentação
        self._create_documentation(project_dir, config)
        
        return {
            'success': True,
            'project_path': project_dir,
            'config': config,
            'files_created': self._count_files(project_dir),
            'mobile_first': True,
            'pwa_ready': True,
            'artifact_location': 'ARTEFATOS'
        }
    
    def _create_main_files(self, project_dir: str, config: Dict[str, Any]):
        """Cria os arquivos principais do projeto."""
        
        # index.html principal
        index_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#111827">
    <title>{config['project_name']}</title>
    <link rel="manifest" href="/manifest.webmanifest">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    {"<script src='https://cdn.tailwindcss.com'></script>" if config['css_lib'] == 'tailwind' else ""}
    <style>
        /* Mobile-first CSS */
        * {{ box-sizing: border-box; }}
        html {{ font-size: 16px; line-height: 1.6; }}
        body {{ margin: 0; font-family: system-ui, sans-serif; }}
        .container {{ max-width: 100%; padding: 1rem; }}
        @media (min-width: 768px) {{ .container {{ max-width: 768px; margin: 0 auto; }} }}
        @media (min-width: 1024px) {{ .container {{ max-width: 1024px; }} }}
        
        /* Loading animation */
        .loading {{ animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
    </style>
</head>
<body>
    <div id="app" class="container">
        <header class="sticky top-0 bg-white/70 backdrop-blur z-10 border-b mb-6">
            <div class="flex items-center justify-between py-4">
                <h1 class="text-xl font-bold">{config['project_name']}</h1>
                <nav class="flex gap-4">
                    <a href="#home" class="text-sm hover:text-blue-600">Home</a>
                    <a href="#about" class="text-sm hover:text-blue-600">Sobre</a>
                </nav>
            </div>
        </header>
        
        <main>
            <section id="home" class="mb-8">
                <h2 class="text-2xl font-bold mb-4">Bem-vindo!</h2>
                <p class="text-gray-600 mb-6">Este é um aplicativo mobile-first com PWA e suporte offline.</p>
                
                <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <div class="p-4 border rounded-lg shadow-sm">
                        <h3 class="font-bold mb-2">📱 Mobile-First</h3>
                        <p class="text-sm text-gray-600">Otimizado para dispositivos móveis</p>
                    </div>
                    <div class="p-4 border rounded-lg shadow-sm">
                        <h3 class="font-bold mb-2">⚡ PWA</h3>
                        <p class="text-sm text-gray-600">Funciona offline e pode ser instalado</p>
                    </div>
                    <div class="p-4 border rounded-lg shadow-sm">
                        <h3 class="font-bold mb-2">🎨 Responsivo</h3>
                        <p class="text-sm text-gray-600">Adapta-se a qualquer tela</p>
                    </div>
                </div>
                
                <div class="mt-8">
                    <button id="installBtn" class="hidden px-6 py-3 bg-blue-600 text-white rounded-lg font-medium">
                        📱 Instalar App
                    </button>
                    <button onclick="testNotification()" class="ml-4 px-6 py-3 bg-green-600 text-white rounded-lg font-medium">
                        🔔 Testar Notificação
                    </button>
                </div>
            </section>
        </main>
        
        <footer class="mt-12 py-8 border-t text-center text-sm text-gray-500">
            <p>&copy; 2025 {config['author']} - {config['project_name']}</p>
        </footer>
    </div>

    <script>
        // PWA Installation
        let deferredPrompt;
        const installBtn = document.getElementById('installBtn');

        window.addEventListener('beforeinstallprompt', (e) => {{
            e.preventDefault();
            deferredPrompt = e;
            installBtn.classList.remove('hidden');
        }});

        installBtn.addEventListener('click', async () => {{
            if (deferredPrompt) {{
                deferredPrompt.prompt();
                const result = await deferredPrompt.userChoice;
                console.log('Install result:', result);
                deferredPrompt = null;
                installBtn.classList.add('hidden');
            }}
        }});

        // Service Worker Registration
        if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/sw.js')
                .then(reg => console.log('SW registered:', reg))
                .catch(err => console.log('SW registration failed:', err));
        }}

        // Notification API
        async function testNotification() {{
            if ('Notification' in window) {{
                const permission = await Notification.requestPermission();
                if (permission === 'granted') {{
                    new Notification('Teste de Notificação', {{
                        body: 'Seu app mobile-first está funcionando perfeitamente!',
                        icon: '/icon-192x192.png'
                    }});
                }}
            }}
        }}

        // Touch gestures for mobile
        let touchStartX = 0;
        let touchStartY = 0;

        document.addEventListener('touchstart', e => {{
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
        }});

        document.addEventListener('touchend', e => {{
            const touchEndX = e.changedTouches[0].screenX;
            const touchEndY = e.changedTouches[0].screenY;
            handleGesture(touchStartX, touchStartY, touchEndX, touchEndY);
        }});

        function handleGesture(startX, startY, endX, endY) {{
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {{
                if (deltaX > 0) {{
                    console.log('Swipe right');
                }} else {{
                    console.log('Swipe left');
                }}
            }}
        }}
    </script>
</body>
</html>"""
        
        with open(os.path.join(project_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
    
    def _setup_pwa(self, project_dir: str, config: Dict[str, Any]):
        """Configura PWA com manifest e service worker."""
        
        # manifest.webmanifest
        manifest = {
            "name": config['project_name'],
            "short_name": config['project_name'][:12],
            "description": config['description'],
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#111827",
            "icons": [
                {
                    "src": "/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/icon-512x512.png", 
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }
        
        import json
        with open(os.path.join(project_dir, 'public', 'manifest.webmanifest'), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        # Service Worker
        sw_js = """
const CACHE_NAME = 'mobile-first-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.webmanifest'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});
"""
        
        with open(os.path.join(project_dir, 'sw.js'), 'w', encoding='utf-8') as f:
            f.write(sw_js)
    
    def _create_ui_components(self, project_dir: str, config: Dict[str, Any]):
        """Cria componentes UI responsivos."""
        
        components_dir = os.path.join(project_dir, 'src', 'components')
        os.makedirs(components_dir, exist_ok=True)
        
        # Component principal React (se usando React)
        if config['ui_lib'] == 'react':
            main_component = f"""import React, {{ useState, useEffect }} from 'react';

export default function MobileFirstApp() {{
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [count, setCount] = useState(0);

  useEffect(() => {{
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {{
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    }};
  }}, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {{/* Status bar */}}
      <div className={{`fixed top-0 left-0 right-0 z-50 px-4 py-2 text-center text-sm 
        ${{isOnline ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}}`}}>
        {{isOnline ? '🟢 Online' : '🔴 Offline'}}
      </div>

      {{/* Main content */}}
      <main className="pt-12 px-4 pb-20">
        <div className="max-w-md mx-auto">
          <h1 className="text-2xl font-bold text-center mb-8">
            {config['project_name']}
          </h1>

          {{/* Interactive counter */}}
          <div className="bg-white rounded-lg p-6 shadow-lg mb-6">
            <h2 className="text-lg font-semibold mb-4">Contador Interativo</h2>
            <div className="flex items-center justify-between">
              <button 
                onClick={{() => setCount(c => Math.max(0, c - 1))}}
                className="w-12 h-12 bg-red-500 text-white rounded-full text-xl font-bold active:scale-95 transition-transform"
              >
                -
              </button>
              <span className="text-3xl font-bold text-gray-800">{{count}}</span>
              <button 
                onClick={{() => setCount(c => c + 1)}}
                className="w-12 h-12 bg-green-500 text-white rounded-full text-xl font-bold active:scale-95 transition-transform"
              >
                +
              </button>
            </div>
          </div>

          {{/* Features grid */}}
          <div className="grid grid-cols-2 gap-4">
            <FeatureCard 
              icon="📱" 
              title="Mobile-First" 
              description="Otimizado para mobile"
            />
            <FeatureCard 
              icon="⚡" 
              title="PWA Ready" 
              description="Instalável como app"
            />
            <FeatureCard 
              icon="🔄" 
              title="Offline Support" 
              description="Funciona sem internet"
            />
            <FeatureCard 
              icon="🎨" 
              title="Responsivo" 
              description="Adapta-se a telas"
            />
          </div>
        </div>
      </main>

      {{/* Bottom navigation */}}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t">
        <div className="flex justify-around py-2">
          <NavButton icon="🏠" label="Home" active={{true}} />
          <NavButton icon="⚙️" label="Config" />
          <NavButton icon="📊" label="Stats" />
          <NavButton icon="👤" label="Profile" />
        </div>
      </nav>
    </div>
  );
}}

function FeatureCard({{ icon, title, description }}) {{
  return (
    <div className="bg-white rounded-lg p-4 shadow-md text-center">
      <div className="text-2xl mb-2">{{icon}}</div>
      <h3 className="font-semibold text-sm mb-1">{{title}}</h3>
      <p className="text-xs text-gray-600">{{description}}</p>
    </div>
  );
}}

function NavButton({{ icon, label, active = false }}) {{
  return (
    <button className={{`flex flex-col items-center py-2 px-4 rounded-lg transition-colors
      ${{active ? 'text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-blue-600'}}`}}>
      <span className="text-lg">{{icon}}</span>
      <span className="text-xs mt-1">{{label}}</span>
    </button>
  );
}}"""
            
            with open(os.path.join(components_dir, 'MobileFirstApp.jsx'), 'w', encoding='utf-8') as f:
                f.write(main_component)
    
    def _setup_build_scripts(self, project_dir: str, config: Dict[str, Any]):
        """Configura scripts de build e package.json."""
        
        package_json = {
            "name": config['project_name'],
            "version": "1.0.0",
            "description": config['description'],
            "scripts": {
                "dev": "vite --host",
                "build": "vite build",
                "preview": "vite preview --host",
                "pwa": "vite build && vite preview",
                "android": "vite build && cap sync android && cap open android"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "@vitejs/plugin-react": "^4.0.0",
                "vite": "^5.0.0",
                "vite-plugin-pwa": "^0.16.0",
                "tailwindcss": "^3.3.0",
                "autoprefixer": "^10.4.0",
                "postcss": "^8.4.0"
            }
        }
        
        if 'android' in config['target_envs']:
            package_json['dependencies'].update({
                "@capacitor/core": "^5.0.0",
                "@capacitor/cli": "^5.0.0",
                "@capacitor/android": "^5.0.0"
            })
        
        import json
        with open(os.path.join(project_dir, 'package.json'), 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2)
    
    def _create_documentation(self, project_dir: str, config: Dict[str, Any]):
        """Cria documentação do projeto."""
        
        readme = f"""# {config['project_name']}

{config['description']}

## 🚀 Características

- ✅ **Mobile-First**: Otimizado para dispositivos móveis
- ✅ **PWA Ready**: Pode ser instalado como aplicativo nativo
- ✅ **Responsivo**: Adapta-se a qualquer tamanho de tela
- ✅ **Offline Support**: Funciona sem conexão com internet
- ✅ **Fast Loading**: Carregamento ultra-rápido
- ✅ **Touch Optimized**: Gestos e interações otimizadas para touch

## 📱 Instalação

```bash
cd {config['project_name']}
npm install
npm run dev
```

## 🔧 Scripts Disponíveis

- `npm run dev` - Servidor de desenvolvimento
- `npm run build` - Build de produção
- `npm run preview` - Preview da build
- `npm run pwa` - Build e preview PWA
- `npm run android` - Build para Android (requer Capacitor)

## 🎯 Funcionalidades

### PWA (Progressive Web App)
- Instalação nativa em dispositivos
- Cache offline automático
- Notificações push
- Background sync

### Mobile-First Design
- Interface otimizada para mobile
- Navegação por gestos
- Bottom navigation
- Touch-friendly buttons

### Responsividade
- Grid system adaptativo
- Breakpoints mobile/tablet/desktop
- Tipografia escalável
- Imagens responsivas

## 🛠️ Tecnologias

- **Frontend**: {config['ui_lib'].title()}
- **Styling**: {config['css_lib'].title()}
- **Build**: Vite
- **PWA**: Vite Plugin PWA
- **Mobile**: Capacitor (opcional)

## 📂 Estrutura

```
{config['project_name']}/
├── src/
│   ├── components/          # Componentes reutilizáveis
│   └── styles/             # Estilos globais
├── public/
│   ├── manifest.webmanifest # Manifest PWA
│   └── icons/              # Ícones do app
├── sw.js                   # Service Worker
├── index.html              # Entry point
└── package.json           # Dependências
```

## 🚀 Deploy

### Vercel
```bash
npm run build
npx vercel --prod
```

### Netlify
```bash
npm run build
# Fazer upload da pasta dist/
```

### Capacitor (Android)
```bash
npm run android
# Abrir Android Studio e fazer build
```

## 📝 Próximos Passos

1. Personalizar cores e branding
2. Adicionar autenticação
3. Integrar APIs
4. Configurar notificações push
5. Otimizar performance
6. Testes automatizados

## 👤 Autor

{config['author']}

## 📄 Licença

MIT License
"""
        
        with open(os.path.join(project_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme)
    
    def _count_files(self, project_dir: str) -> int:
        """Conta o número de arquivos criados."""
        count = 0
        for root, dirs, files in os.walk(project_dir):
            count += len(files)
        return count

# Registrar cadeia no router HMP
def register_mobile_first_chain():
    """Registra a cadeia mobile-first no sistema HMP."""
    mobile_first_chain = """
SET project_request TO {user_input}
SET mobile_config TO {mobile_config} OR {{}}

# FASE 1: ANÁLISE DE REQUISITOS MOBILE
CALL analyze_mobile_requirements WITH request = project_request
SET requirements TO analysis_result

# FASE 2: CONFIGURAÇÃO DO PROJETO
CALL setup_mobile_project WITH
    name = requirements.project_name,
    type = requirements.project_type,
    features = requirements.features

# FASE 3: GERAÇÃO MOBILE-FIRST
CALL mobile_first_development_chain.execute_mobile_first_pipeline WITH
    project_config = mobile_config

# FASE 4: OTIMIZAÇÃO PWA
CALL optimize_pwa_features WITH project = created_project
CALL setup_offline_capabilities WITH project = optimized_project

# FASE 5: VALIDAÇÃO MOBILE
CALL validate_mobile_responsiveness WITH project = final_project
CALL test_pwa_installation WITH project = validated_project

RETURN mobile_first_project
"""
    
    return mobile_first_chain
