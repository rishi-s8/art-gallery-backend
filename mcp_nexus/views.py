from django.http import HttpRequest, HttpResponse


def home_view(_: HttpRequest):
    return HttpResponse("""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Nanda Registry</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {
                --primary: #8B0000; /* Crimson */
                --primary-light: #A52A2A; /* Lighter Crimson */
                --primary-dark: #5A0000; /* Darker Crimson */
                --secondary: #FFD700; /* Gold */
                --text-on-primary: #FFFFFF; /* White */
                --text-primary: #FFFFFF; /* White */
                --text-secondary: #D3D3D3; /* Light Gray */
                --background: #1C1C1C; /* Very Dark Gray */
                --card-bg: rgba(255, 255, 255, 0.1); /* Glassmorphism effect */
                --border-radius: 12px;
                --transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
                --backdrop-filter: blur(10px); /* Glassmorphism blur */
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--background);
                background-image: none;
                color: var(--text-primary);
                line-height: 1.6;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }

            header {
                background: linear-gradient(135deg, var(--primary), var(--primary-dark));
                color: var(--text-on-primary);
                padding: 2.5rem 1rem;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                position: relative;
                overflow: hidden;
            }

            .header-content {
                max-width: 1200px;
                margin: 0 auto;
                position: relative;
                z-index: 2;
            }

            .header-bg {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                opacity: 0.1;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='152' height='152' viewBox='0 0 152 152'%3E%3Cg fill-rule='evenodd'%3E%3Cg id='temple' fill='%23ffffff' fill-opacity='0.2'%3E%3Cpath d='M152 150v2H0v-2h28v-8H8v-20H0v-2h8V80h42v20h20v42H30v8h90v-8H80v-42h20V80h42v40h8V30h-8v40h-42V50H80V8h40V0h2v8h20v20h8V0h2v150zm-2 0v-28h-8v20h-20v8h28zM82 30v18h18V30H82zm20 18h20v20h18V30h-20V10H82v18h20v20zm0 2v18h18V50h-18zm20-22h18V10h-18v18zm-54 92v-18H50v18h18zm-20-18H28V82H10v38h20v20h38v-18H48v-20zm0-2V82H30v18h18zm-20 22H10v18h18v-18zm54 0v18h38v-20h20V82h-18v20h-20v20H82z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            }

            .logo {
                width: 80px;
                height: 80px;
                background-color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1.5rem;
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
                overflow: hidden;
            }

            .logo i {
                font-size: 42px;
                color: var(--primary);
            }

            h1 {
                font-size: 2.8rem;
                margin-bottom: 0.8rem;
                font-weight: 700;
                letter-spacing: -0.5px;
            }

            .subtitle {
                font-size: 1.2rem;
                opacity: 0.9;
                max-width: 600px;
                margin: 0 auto;
                font-weight: 300;
            }

            main {
                flex: 1;
                max-width: 1200px;
                margin: 0 auto;
                padding: 3rem 1rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }

            .wave {
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 50px;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 320'%3E%3Cpath fill='%23f8f9fa' fill-opacity='1' d='M0,96L48,128C96,160,192,224,288,224C384,224,480,160,576,138.7C672,117,768,139,864,165.3C960,192,1056,224,1152,218.7C1248,213,1344,171,1392,149.3L1440,128L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z'%3E%3C/path%3E%3C/svg%3E");
                background-size: cover;
            }

            .card {
                background-color: var(--card-bg);
                border-radius: var(--border-radius);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                padding: 3rem;
                width: 100%;
                max-width: 900px;
                text-align: center;
                transition: var(--transition);
                position: relative;
                overflow: hidden;
                backdrop-filter: var(--backdrop-filter); /* Glassmorphism effect */
                border: 1px solid rgba(255, 255, 255, 0.2); /* Subtle border for glass effect */
            }

            .card:before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 5px;
                background: linear-gradient(90deg, var(--primary), var(--secondary));
            }

            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
            }

            .intro {
                margin-bottom: 3rem;
            }

            .intro h2 {
                font-size: 2.2rem;
                margin-bottom: 1rem;
                color: var(--primary);
            }

            .intro p {
                color: var(--text-secondary);
                max-width: 600px;
                margin: 0 auto;
                font-size: 1.1rem;
            }

            .cta-button {
                display: inline-block;
                background-color: var(--primary);
                color: white;
                padding: 0.8rem 2rem;
                border-radius: 30px;
                text-decoration: none;
                font-weight: 600;
                margin-top: 1.5rem;
                box-shadow: 0 4px 10px rgba(44, 62, 80, 0.2);
                transition: var(--transition);
            }

            .cta-button:hover {
                background-color: var(--primary-dark);
                transform: translateY(-2px);
                box-shadow: 0 6px 15px rgba(44, 62, 80, 0.3);
            }

            .links-container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin-top: 2rem;
                width: 100%;
            }

            .link-card {
                background-color: var(--card-bg);
                border-radius: var(--border-radius);
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 2rem 1rem;
                transition: var(--transition);
                display: flex;
                flex-direction: column;
                align-items: center;
                text-decoration: none;
                color: var(--text-primary);
                position: relative;
                overflow: hidden;
                backdrop-filter: var(--backdrop-filter);
            }

            .link-card:before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: var(--primary);
                transform: scaleX(0);
                transition: var(--transition);
            }

            .link-card:hover:before {
                transform: scaleX(1);
            }

            .link-card:hover {
                background-color: var(--primary);
                color: var(--text-on-primary);
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(44, 62, 80, 0.3);
            }

            .link-card i {
                font-size: 2.5rem;
                margin-bottom: 1rem;
                transition: var(--transition);
            }

            .link-card:hover i {
                transform: scale(1.2);
            }

            .link-card span {
                font-weight: 500;
                display: block;
                margin-bottom: 0.3rem;
                font-size: 1.1rem;
            }

            .link-card small {
                opacity: 0.8;
                font-size: 0.9rem;
                transition: var(--transition);
            }

            .link-card:hover small {
                color: var(--text-on-primary);
            }

            footer {
                text-align: center;
                padding: 2rem;
                color: var(--text-secondary);
                font-size: 0.9rem;
                margin-top: 2rem;
                border-top: 1px solid rgba(255,255,255,0.1);
                background-color: var(--card-bg);
            }

            .footer-links {
                display: flex;
                justify-content: center;
                gap: 1.5rem;
                margin-top: 1rem;
            }

            .footer-links a {
                color: var(--text-secondary);
                text-decoration: none;
                transition: var(--transition);
            }

            .footer-links a:hover {
                color: var(--secondary);
            }

            .status {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-top: 1.5rem;
                font-size: 0.85rem;
            }

            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #4caf50;
                margin-right: 6px;
                position: relative;
            }

            .status-indicator:after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background-color: #4caf50;
                opacity: 0.5;
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0% {
                    transform: scale(1);
                    opacity: 0.5;
                }
                50% {
                    transform: scale(2.5);
                    opacity: 0;
                }
                100% {
                    transform: scale(1);
                    opacity: 0;
                }
            }

            @media (max-width: 768px) {
                h1 {
                    font-size: 2.2rem;
                }

                .intro h2 {
                    font-size: 1.8rem;
                }

                .links-container {
                    grid-template-columns: 1fr;
                }

                .card {
                    padding: 2rem 1.5rem;
                }

                .logo {
                    width: 70px;
                    height: 70px;
                }

                .logo i {
                    font-size: 36px;
                }

                .footer-links {
                    flex-direction: column;
                    gap: 0.8rem;
                }
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes scaleIn {
                from { transform: scale(0.8); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }

            @keyframes slideInRight {
                from { transform: translateX(50px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }

            .fadeIn {
                animation: fadeIn 0.8s ease-out forwards;
            }

            .scaleIn {
                animation: scaleIn 0.5s ease-out forwards;
            }

            .slideIn {
                animation: slideInRight 0.5s ease-out forwards;
            }

            .delay-1 {
                animation-delay: 0.1s;
            }

            .delay-2 {
                animation-delay: 0.2s;
            }

            .delay-3 {
                animation-delay: 0.3s;
            }

            .delay-4 {
                animation-delay: 0.4s;
            }
        </style>
    </head>
    <body>
        <header>
            <div class="header-bg"></div>
            <div class="header-content">
                <div class="logo scaleIn">
                    <i class="fas fa-heartbeat"></i>
                </div>
                <h1 class="fadeIn">Nanda Registry</h1>
                <p class="subtitle fadeIn delay-1">Towards Decentralized AI</p>
            </div>
            <div class="wave"></div>
        </header>

        <main>
            <div class="card fadeIn delay-2">
                <div class="intro">
                    <h2>Welcome to the Registry Server</h2>
                    <p>The registry server provides a list of available Agents, Resources and Tools.</p>
                    <a href="/api/docs/" class="cta-button">Get Started</a>
                </div>

                <div class="links-container">
                    <a href="/admin/" class="link-card slideIn delay-1">
                        <i class="fas fa-user-shield"></i>
                        <span>Admin Panel</span>
                        <small>Manage registry data</small>
                    </a>
                    <a href="/api/v1/" class="link-card slideIn delay-2">
                        <i class="fas fa-code"></i>
                        <span>API v1</span>
                        <small>Access endpoints</small>
                    </a>
                    <a href="/api/docs/" class="link-card slideIn delay-3">
                        <i class="fas fa-book"></i>
                        <span>API Documentation</span>
                        <small>Swagger UI</small>
                    </a>
                    <a href="/api/redoc/" class="link-card slideIn delay-4">
                        <i class="fas fa-file-alt"></i>
                        <span>API Documentation</span>
                        <small>ReDoc Interface</small>
                    </a>
                </div>
            </div>
        </main>

        <footer>
            <p>&copy; 2025 Nanda Registry - A MIT Media Lab Project</p>
            <div class="footer-links">
                <a href="#">Privacy Policy</a>
                <a href="#">Terms of Service</a>
                <a href="#">Contact</a>
            </div>
            <div class="status">
                <div class="status-indicator"></div>
                <span>All systems operational</span>
            </div>
        </footer>
    </body>
    </html>
    """)