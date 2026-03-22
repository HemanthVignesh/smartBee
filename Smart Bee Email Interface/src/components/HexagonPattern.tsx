export function HexagonPattern() {
  return (
    <div className="absolute inset-0 opacity-5 pointer-events-none overflow-hidden">
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="hexagons" width="100" height="86.6" patternUnits="userSpaceOnUse">
            <path
              d="M25 0 L75 0 L100 43.3 L75 86.6 L25 86.6 L0 43.3 Z"
              fill="none"
              stroke="url(#hexGradient)"
              strokeWidth="1.5"
              className="animate-pulse"
              style={{ animationDuration: "4s" }}
            />
          </pattern>
          <linearGradient id="hexGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFC107" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#FFB300" stopOpacity="1" />
            <stop offset="100%" stopColor="#FFCA28" stopOpacity="0.6" />
          </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#hexagons)" />
      </svg>
      
      {/* Animated gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#FFF8E1]/20 via-transparent to-[#FFC107]/10 animate-pulse" style={{ animationDuration: "6s" }}></div>
    </div>
  );
}