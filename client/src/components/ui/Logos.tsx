import React from 'react';

interface LogoProps {
  className?: string;
  size?: number;
}

// 1. Primary UrbanSync AI Platform Logo
export const UrbanSyncLogo: React.FC<LogoProps> = ({ className = 'w-8 h-8', size }) => (
  <svg
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={size ? { width: size, height: size } : undefined}
  >
    <defs>
      <linearGradient id="us-grad-primary" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#06B6D4" />
        <stop offset="50%" stopColor="#3B82F6" />
        <stop offset="100%" stopColor="#10B981" />
      </linearGradient>
      <linearGradient id="us-glow" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.8" />
        <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.8" />
      </linearGradient>
      <filter id="us-shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#06B6D4" floodOpacity="0.4" />
      </filter>
    </defs>
    
    {/* Outer Hexagonal Mesh Shield */}
    <path
      d="M32 4L56 18V46L32 60L8 46V18L32 4Z"
      stroke="url(#us-grad-primary)"
      strokeWidth="2.5"
      fill="rgba(6, 182, 212, 0.08)"
      filter="url(#us-shadow)"
    />
    
    {/* Isometric Digital Twin City Blocks */}
    <path
      d="M32 14L45 22V37L32 45L19 37V22L32 14Z"
      fill="url(#us-glow)"
      fillOpacity="0.2"
      stroke="#06B6D4"
      strokeWidth="1.5"
    />
    
    {/* Internal Twin Nodes */}
    <path d="M32 14V45" stroke="#38BDF8" strokeWidth="1.5" strokeDasharray="2 2" />
    <path d="M19 22L32 30L45 22" stroke="#38BDF8" strokeWidth="1.5" />
    <path d="M19 37L32 30L45 37" stroke="#10B981" strokeWidth="1.5" />
    
    {/* Central Pulsing Mesh Core */}
    <circle cx="32" cy="30" r="4.5" fill="#06B6D4" />
    <circle cx="32" cy="30" r="7" stroke="#38BDF8" strokeWidth="1.2" strokeOpacity="0.7">
      <animate attributeName="r" values="5;8;5" dur="3s" repeatCount="indefinite" />
      <animate attributeName="stroke-opacity" values="0.8;0.2;0.8" dur="3s" repeatCount="indefinite" />
    </circle>
  </svg>
);

// 2. UrbanSync Sanitation & CVRP Engine Logo (Green Waste Loop)
export const SanitationCoreLogo: React.FC<LogoProps> = ({ className = 'w-6 h-6', size }) => (
  <svg
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={size ? { width: size, height: size } : undefined}
  >
    <defs>
      <linearGradient id="san-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#10B981" />
        <stop offset="100%" stopColor="#059669" />
      </linearGradient>
    </defs>
    {/* Circular eco-loop with bin telemetry */}
    <circle cx="24" cy="24" r="20" stroke="url(#san-grad)" strokeWidth="2.5" strokeDasharray="7 3" />
    {/* Smart Bin Silhouette */}
    <path
      d="M17 17H31M19 17L20.5 33C20.6 34.1 21.5 35 22.6 35H25.4C26.5 35 27.4 34.1 27.5 33L29 17"
      stroke="#10B981"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M21 14C21 12.9 21.9 12 23 12H25C26.1 12 27 12.9 27 14" stroke="#34D399" strokeWidth="2" strokeLinecap="round" />
    {/* Fill Level Metric Bars */}
    <line x1="22" y1="23" x2="26" y2="23" stroke="#34D399" strokeWidth="1.8" strokeLinecap="round" />
    <line x1="23" y1="27" x2="25" y2="27" stroke="#34D399" strokeWidth="1.8" strokeLinecap="round" />
    {/* Telemetry pulse beacon */}
    <circle cx="34" cy="14" r="3" fill="#10B981" />
    <circle cx="34" cy="14" r="5" stroke="#10B981" strokeWidth="1" strokeOpacity="0.5" />
  </svg>
);

// 3. SILN Mobility & LogPose Engine Logo (Green Wave Transit Vector)
export const MobilitySilnLogo: React.FC<LogoProps> = ({ className = 'w-6 h-6', size }) => (
  <svg
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={size ? { width: size, height: size } : undefined}
  >
    <defs>
      <linearGradient id="mob-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#06B6D4" />
        <stop offset="100%" stopColor="#3B82F6" />
      </linearGradient>
    </defs>
    {/* Outer compass navigation ring */}
    <circle cx="24" cy="24" r="20" stroke="url(#mob-grad)" strokeWidth="2.5" />
    {/* Green Wave Corridors */}
    <path
      d="M12 28C16 22 20 22 24 28C28 34 32 34 36 28"
      stroke="#38BDF8"
      strokeWidth="2.5"
      strokeLinecap="round"
    />
    <path
      d="M12 22C16 16 20 16 24 22C28 28 32 28 36 22"
      stroke="#06B6D4"
      strokeWidth="2"
      strokeOpacity="0.6"
      strokeLinecap="round"
    />
    {/* LogPose Navigation Arrow Needle */}
    <polygon points="24,10 27,22 24,19 21,22" fill="#38BDF8" />
    <circle cx="24" cy="24" r="3" fill="#06B6D4" />
  </svg>
);

// 4. Nirbhaya-Mesh v3.7 Safety Engine Logo (Optical Radar Shield)
export const NirbhayaSafetyLogo: React.FC<LogoProps> = ({ className = 'w-6 h-6', size }) => (
  <svg
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={size ? { width: size, height: size } : undefined}
  >
    <defs>
      <linearGradient id="safe-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#EC4899" />
        <stop offset="50%" stopColor="#8B5CF6" />
        <stop offset="100%" stopColor="#06B6D4" />
      </linearGradient>
    </defs>
    {/* Shield Silhouette */}
    <path
      d="M24 6L38 12V24C38 33 32 39 24 42C16 39 10 33 10 24V12L24 6Z"
      stroke="url(#safe-grad)"
      strokeWidth="2.5"
      fill="rgba(236, 72, 153, 0.08)"
    />
    {/* Concentric CCTV Radar Cones */}
    <path d="M24 16L32 30H16L24 16Z" fill="#EC4899" fillOpacity="0.25" stroke="#EC4899" strokeWidth="1.5" />
    <circle cx="24" cy="18" r="2.5" fill="#38BDF8" />
    {/* Pink Booth Cross / Protection Emblem */}
    <path d="M24 23V29M21 26H27" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

// 5. Official UP-112 CAD Emergency Police Dispatch Seal
export const UP112CadLogo: React.FC<LogoProps> = ({ className = 'w-6 h-6', size }) => (
  <svg
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={size ? { width: size, height: size } : undefined}
  >
    <defs>
      <linearGradient id="up112-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#EF4444" />
        <stop offset="100%" stopColor="#B91C1C" />
      </linearGradient>
    </defs>
    {/* Police Cad Octagonal Badge */}
    <polygon points="15,5 33,5 43,15 43,33 33,43 15,43 5,33 5,15" fill="url(#up112-grad)" stroke="#FCA5A5" strokeWidth="1.5" />
    {/* Golden Emergency Star */}
    <circle cx="24" cy="24" r="13" fill="#1E293B" stroke="#FBBF24" strokeWidth="1.5" />
    <text
      x="24"
      y="27.5"
      textAnchor="middle"
      fontSize="9.5"
      fontWeight="900"
      fontFamily="monospace"
      fill="#FBBF24"
      letterSpacing="0.5"
    >
      112
    </text>
    <text
      x="24"
      y="18"
      textAnchor="middle"
      fontSize="5.5"
      fontWeight="700"
      fontFamily="sans-serif"
      fill="#94A3B8"
    >
      UP-CAD
    </text>
  </svg>
);

// 6. Google OR-Tools Mathematical Optimization Solver Logo
export const ORToolsLogo: React.FC<LogoProps> = ({ className = 'w-5 h-5', size }) => (
  <svg
    viewBox="0 0 32 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={size ? { width: size, height: size } : undefined}
  >
    {/* Graph network nodes connected by shortest path edges */}
    <path d="M7 23L16 9L25 23" stroke="#4285F4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M7 23H25" stroke="#34A853" strokeWidth="2" strokeLinecap="round" />
    <path d="M16 9V23" stroke="#EA4335" strokeWidth="1.5" strokeDasharray="2 2" />
    <circle cx="16" cy="9" r="4" fill="#4285F4" stroke="#FFFFFF" strokeWidth="1.2" />
    <circle cx="7" cy="23" r="3.5" fill="#EA4335" stroke="#FFFFFF" strokeWidth="1.2" />
    <circle cx="25" cy="23" r="3.5" fill="#34A853" stroke="#FFFFFF" strokeWidth="1.2" />
  </svg>
);

// 7. City of Lucknow Smart City Digital Twin Crest
export const LucknowCivicLogo: React.FC<LogoProps> = ({ className = 'w-5 h-5', size }) => (
  <svg
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={size ? { width: size, height: size } : undefined}
  >
    {/* Royal Architectural Gate / Rumi Darwaza Silhouette Motif */}
    <circle cx="18" cy="18" r="16" fill="rgba(6, 182, 212, 0.12)" stroke="#06B6D4" strokeWidth="1.5" />
    <path
      d="M11 26V18C11 14.1 14.1 11 18 11C21.9 11 25 14.1 25 18V26"
      stroke="#38BDF8"
      strokeWidth="2"
      strokeLinecap="round"
    />
    <path
      d="M15 26V20C15 18.3 16.3 17 18 17C19.7 17 21 18.3 21 20V26"
      stroke="#10B981"
      strokeWidth="1.5"
    />
    <circle cx="18" cy="8" r="1.5" fill="#F59E0B" />
  </svg>
);
