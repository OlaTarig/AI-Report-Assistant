interface Props {
  className?: string;
}

export default function Mascot({ className = "h-10 w-10" }: Props) {
  return (
    <svg viewBox="0 0 120 120" className={className} aria-label="Captain Draft" role="img">
      {/* Cape — drawn first so it renders behind the pencil body */}
      <g transform="rotate(-35 60 60)">
        <path
          d="M 92 52 C 112 58, 122 78, 116 100 C 104 90, 98 76, 88 66 Z"
          fill="#E0800A"
        />
        <path
          d="M 90 55 C 105 62, 112 78, 108 94 C 99 85, 94 74, 86 65 Z"
          fill="#FF971D"
        />
      </g>

      {/* Pencil body, flying diagonally like a classic superhero pose */}
      <g transform="rotate(-35 60 60)">
        {/* Graphite tip */}
        <polygon points="14,58 14,64 3,61" fill="#3A2E2A" />
        {/* Wood taper */}
        <polygon points="25,54 25,68 14,61" fill="#FF971D" />
        {/* Barrel */}
        <rect x="25" y="54" width="63" height="14" rx="3" fill="#FFE8D6" stroke="#3A2E2A" strokeWidth="2" />
        {/* Ferrule (metal band) */}
        <rect x="88" y="52" width="7" height="18" fill="#FFFFFF" stroke="#3A2E2A" strokeWidth="2" />
        {/* Eraser */}
        <rect x="95" y="51" width="15" height="20" rx="4" fill="#FF971D" stroke="#3A2E2A" strokeWidth="2" />

        {/* Face */}
        <circle cx="58" cy="58" r="2.2" fill="#3A2E2A" />
        <circle cx="67" cy="58" r="2.2" fill="#3A2E2A" />
        <path d="M 59 64 Q 63 67, 68 64" stroke="#3A2E2A" strokeWidth="2" fill="none" strokeLinecap="round" />
      </g>
    </svg>
  );
}