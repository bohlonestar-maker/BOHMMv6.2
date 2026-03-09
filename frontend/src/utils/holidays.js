/**
 * US Federal Holiday Detection and Decoration System
 * 
 * Detects US federal holidays and returns appropriate decorations
 * for the login page.
 */

// Helper to get nth weekday of a month
const getNthWeekdayOfMonth = (year, month, weekday, n) => {
  const firstDay = new Date(year, month, 1);
  let dayOfWeek = firstDay.getDay();
  let diff = weekday - dayOfWeek;
  if (diff < 0) diff += 7;
  const firstOccurrence = 1 + diff;
  return new Date(year, month, firstOccurrence + (n - 1) * 7);
};

// Get last weekday of a month
const getLastWeekdayOfMonth = (year, month, weekday) => {
  const lastDay = new Date(year, month + 1, 0);
  let dayOfWeek = lastDay.getDay();
  let diff = dayOfWeek - weekday;
  if (diff < 0) diff += 7;
  return new Date(year, month + 1, -diff);
};

// Check if a date is the observed holiday (for weekends)
const getObservedDate = (date) => {
  const day = date.getDay();
  if (day === 0) return new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1); // Sunday -> Monday
  if (day === 6) return new Date(date.getFullYear(), date.getMonth(), date.getDate() - 1); // Saturday -> Friday
  return date;
};

// Check if two dates are the same day
const isSameDay = (date1, date2) => {
  return date1.getFullYear() === date2.getFullYear() &&
         date1.getMonth() === date2.getMonth() &&
         date1.getDate() === date2.getDate();
};

/**
 * Detects current US federal holiday
 * @returns {Object|null} Holiday info or null if no holiday
 */
export const getCurrentHoliday = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();
  const date = today.getDate();
  
  // Define all US holidays (Federal + popular)
  const holidays = [
    {
      name: "New Year's Day",
      key: "newyear",
      date: getObservedDate(new Date(year, 0, 1)),
      greeting: "Happy New Year!",
      emoji: "🎆",
      colors: {
        primary: "from-yellow-500 to-orange-500",
        accent: "text-yellow-400",
        bg: "bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900",
        border: "border-yellow-500/30",
        glow: "shadow-yellow-500/20"
      },
      decorations: ["🎆", "🎇", "✨", "🥂", "🎊"]
    },
    {
      name: "Martin Luther King Jr. Day",
      key: "mlk",
      date: getNthWeekdayOfMonth(year, 0, 1, 3), // Third Monday of January
      greeting: "Honoring Dr. King's Legacy",
      emoji: "✊",
      colors: {
        primary: "from-amber-600 to-red-600",
        accent: "text-amber-400",
        bg: "bg-gradient-to-br from-slate-900 via-amber-950 to-slate-900",
        border: "border-amber-500/30",
        glow: "shadow-amber-500/20"
      },
      decorations: ["✊", "🕊️", "💫", "🌟"]
    },
    {
      name: "Valentine's Day",
      key: "valentines",
      date: new Date(year, 1, 14), // February 14
      greeting: "Happy Valentine's Day!",
      emoji: "❤️",
      colors: {
        primary: "from-pink-500 to-red-500",
        accent: "text-pink-400",
        bg: "bg-gradient-to-br from-slate-900 via-pink-950 to-red-950",
        border: "border-pink-500/30",
        glow: "shadow-pink-500/20"
      },
      decorations: ["❤️", "💕", "💘", "🌹", "💝", "💖"]
    },
    {
      name: "Presidents' Day",
      key: "presidents",
      date: getNthWeekdayOfMonth(year, 1, 1, 3), // Third Monday of February
      greeting: "Happy Presidents' Day!",
      emoji: "🇺🇸",
      colors: {
        primary: "from-red-600 to-blue-600",
        accent: "text-red-400",
        bg: "bg-gradient-to-br from-blue-950 via-slate-900 to-red-950",
        border: "border-red-500/30",
        glow: "shadow-red-500/20"
      },
      decorations: ["🇺🇸", "⭐", "🦅", "🗽"]
    },
    {
      name: "St. Patrick's Day",
      key: "stpatricks",
      date: new Date(year, 2, 17), // March 17
      greeting: "Happy St. Patrick's Day!",
      emoji: "☘️",
      colors: {
        primary: "from-green-500 to-emerald-600",
        accent: "text-green-400",
        bg: "bg-gradient-to-br from-slate-900 via-green-950 to-emerald-950",
        border: "border-green-500/30",
        glow: "shadow-green-500/20"
      },
      decorations: ["☘️", "🍀", "🌈", "🪙", "🎩", "💚"]
    },
    {
      name: "Memorial Day",
      key: "memorial",
      date: getLastWeekdayOfMonth(year, 4, 1), // Last Monday of May
      greeting: "Honoring Our Heroes",
      emoji: "🎖️",
      colors: {
        primary: "from-red-700 to-blue-700",
        accent: "text-red-300",
        bg: "bg-gradient-to-br from-blue-950 via-slate-900 to-red-950",
        border: "border-red-500/30",
        glow: "shadow-red-500/20"
      },
      decorations: ["🇺🇸", "🎖️", "⭐", "🕊️", "🌹"]
    },
    {
      name: "Juneteenth",
      key: "juneteenth",
      date: getObservedDate(new Date(year, 5, 19)),
      greeting: "Happy Juneteenth!",
      emoji: "✊",
      colors: {
        primary: "from-red-600 to-green-600",
        accent: "text-red-400",
        bg: "bg-gradient-to-br from-red-950 via-slate-900 to-green-950",
        border: "border-red-500/30",
        glow: "shadow-red-500/20"
      },
      decorations: ["✊", "🎉", "⭐", "🌟", "💫"]
    },
    {
      name: "Independence Day",
      key: "july4th",
      date: getObservedDate(new Date(year, 6, 4)),
      greeting: "Happy 4th of July!",
      emoji: "🎆",
      colors: {
        primary: "from-red-600 via-white to-blue-600",
        accent: "text-red-400",
        bg: "bg-gradient-to-br from-blue-950 via-slate-900 to-red-950",
        border: "border-blue-500/30",
        glow: "shadow-blue-500/20"
      },
      decorations: ["🇺🇸", "🎆", "🎇", "⭐", "🦅", "🗽"]
    },
    {
      name: "Labor Day",
      key: "labor",
      date: getNthWeekdayOfMonth(year, 8, 1, 1), // First Monday of September
      greeting: "Happy Labor Day!",
      emoji: "👷",
      colors: {
        primary: "from-blue-600 to-amber-600",
        accent: "text-blue-400",
        bg: "bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900",
        border: "border-blue-500/30",
        glow: "shadow-blue-500/20"
      },
      decorations: ["👷", "🔧", "⚙️", "🏗️", "💪"]
    },
    {
      name: "Columbus Day",
      key: "columbus",
      date: getNthWeekdayOfMonth(year, 9, 1, 2), // Second Monday of October
      greeting: "Happy Columbus Day!",
      emoji: "⛵",
      colors: {
        primary: "from-blue-600 to-cyan-600",
        accent: "text-cyan-400",
        bg: "bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900",
        border: "border-cyan-500/30",
        glow: "shadow-cyan-500/20"
      },
      decorations: ["⛵", "🌊", "🗺️", "🧭"]
    },
    {
      name: "Veterans Day",
      key: "veterans",
      date: getObservedDate(new Date(year, 10, 11)),
      greeting: "Thank You, Veterans!",
      emoji: "🎖️",
      colors: {
        primary: "from-red-700 to-blue-700",
        accent: "text-amber-400",
        bg: "bg-gradient-to-br from-blue-950 via-slate-900 to-red-950",
        border: "border-amber-500/30",
        glow: "shadow-amber-500/20"
      },
      decorations: ["🇺🇸", "🎖️", "⭐", "🦅", "🏅"]
    },
    {
      name: "Thanksgiving",
      key: "thanksgiving",
      date: getNthWeekdayOfMonth(year, 10, 4, 4), // Fourth Thursday of November
      greeting: "Happy Thanksgiving!",
      emoji: "🦃",
      colors: {
        primary: "from-orange-600 to-amber-600",
        accent: "text-orange-400",
        bg: "bg-gradient-to-br from-slate-900 via-orange-950 to-slate-900",
        border: "border-orange-500/30",
        glow: "shadow-orange-500/20"
      },
      decorations: ["🦃", "🍂", "🌽", "🥧", "🍁"]
    },
    {
      name: "Christmas",
      key: "christmas",
      date: getObservedDate(new Date(year, 11, 25)),
      greeting: "Merry Christmas!",
      emoji: "🎄",
      colors: {
        primary: "from-red-600 to-green-600",
        accent: "text-red-400",
        bg: "bg-gradient-to-br from-green-950 via-slate-900 to-red-950",
        border: "border-red-500/30",
        glow: "shadow-red-500/20"
      },
      decorations: ["🎄", "🎅", "🎁", "⭐", "❄️", "🔔"]
    }
  ];

  // Check each holiday
  for (const holiday of holidays) {
    if (isSameDay(today, holiday.date)) {
      return holiday;
    }
  }

  // Check for day before/after for extended celebrations (Christmas Eve, etc.)
  const christmasEve = new Date(year, 11, 24);
  if (isSameDay(today, christmasEve)) {
    return {
      ...holidays.find(h => h.key === 'christmas'),
      name: "Christmas Eve",
      greeting: "Merry Christmas Eve!"
    };
  }

  const newYearsEve = new Date(year, 11, 31);
  if (isSameDay(today, newYearsEve)) {
    return {
      name: "New Year's Eve",
      key: "newyearseve",
      greeting: "Happy New Year's Eve!",
      emoji: "🎉",
      colors: {
        primary: "from-yellow-500 to-purple-500",
        accent: "text-yellow-400",
        bg: "bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900",
        border: "border-purple-500/30",
        glow: "shadow-purple-500/20"
      },
      decorations: ["🎉", "🎊", "✨", "🥂", "⏰"]
    };
  }

  return null;
};

/**
 * Holiday Decorations Component
 * Renders floating decorations based on the holiday
 */
export const HolidayDecorations = ({ holiday }) => {
  if (!holiday) return null;

  const { decorations } = holiday;

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      {decorations.map((emoji, index) => (
        <div
          key={index}
          className="absolute animate-float text-2xl sm:text-3xl opacity-60"
          style={{
            left: `${10 + (index * 18) % 80}%`,
            top: `${5 + (index * 23) % 70}%`,
            animationDelay: `${index * 0.5}s`,
            animationDuration: `${3 + (index % 3)}s`
          }}
        >
          {emoji}
        </div>
      ))}
      {/* Additional decorations on other side */}
      {decorations.slice(0, 3).map((emoji, index) => (
        <div
          key={`right-${index}`}
          className="absolute animate-float-reverse text-xl sm:text-2xl opacity-40"
          style={{
            right: `${5 + (index * 15) % 30}%`,
            bottom: `${10 + (index * 20) % 50}%`,
            animationDelay: `${index * 0.7}s`,
            animationDuration: `${4 + (index % 2)}s`
          }}
        >
          {emoji}
        </div>
      ))}
    </div>
  );
};

/**
 * Holiday Banner Component
 * Shows a festive greeting banner
 */
export const HolidayBanner = ({ holiday }) => {
  if (!holiday) return null;

  return (
    <div className={`mb-4 px-4 py-2 rounded-lg border ${holiday.colors.border} bg-gradient-to-r ${holiday.colors.primary} bg-opacity-20 backdrop-blur-sm ${holiday.colors.glow} shadow-lg`}>
      <p className="text-center text-white font-medium text-sm flex items-center justify-center gap-2">
        <span className="text-lg">{holiday.emoji}</span>
        {holiday.greeting}
        <span className="text-lg">{holiday.emoji}</span>
      </p>
    </div>
  );
};

export default getCurrentHoliday;
