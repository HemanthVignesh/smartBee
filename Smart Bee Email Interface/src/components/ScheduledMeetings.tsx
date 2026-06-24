import { Calendar, Clock, Users, List, CalendarDays, Video, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { useMeetings } from "../api/client";

interface ScheduledMeeting {
  id: string;
  title: string;
  attendees: string[];
  scheduledTime: string;
  date: string;
  duration: string;
  color?: string;
  priority?: "low" | "medium" | "high";
  meetingLink?: string;
}

const mockMeetings: ScheduledMeeting[] = [
  {
    id: "1",
    title: "Product Strategy Review",
    attendees: ["Alex Chen", "Maria Garcia", "Tom Brown"],
    scheduledTime: "10:00 AM",
    date: "Dec 17, 2025",
    duration: "1h",
    color: "#FFC107",
    priority: "high",
    meetingLink: "https://meet.example.com/abc123"
  },
  {
    id: "2",
    title: "Client Presentation",
    attendees: ["Jennifer Lee", "Robert Smith"],
    scheduledTime: "03:00 PM",
    date: "Dec 17, 2025",
    duration: "45m",
    color: "#FFB300",
    priority: "high",
    meetingLink: "https://zoom.us/j/123456"
  },
  {
    id: "3",
    title: "Sprint Planning Meeting",
    attendees: ["Dev Team", "Product Manager"],
    scheduledTime: "09:30 AM",
    date: "Dec 18, 2025",
    duration: "2h",
    color: "#FFCA28",
    priority: "medium"
  },
  {
    id: "4",
    title: "1:1 with Manager",
    attendees: ["Sarah Johnson"],
    scheduledTime: "04:00 PM",
    date: "Dec 19, 2025",
    duration: "30m",
    color: "#FFD54F",
    priority: "low"
  }
];

type ViewMode = "list" | "calendar";

const priorityDotColors = {
  low: "bg-gray-400",
  medium: "bg-blue-500",
  high: "bg-orange-500"
};

// Generate initials from name
function getInitials(name: string) {
  return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
}

// Generate a color for avatar based on name
function getAvatarColor(name: string) {
  const colors = [
    "bg-blue-500", "bg-green-500", "bg-purple-500", "bg-pink-500", 
    "bg-indigo-500", "bg-yellow-500", "bg-red-500", "bg-teal-500"
  ];
  const index = name.charCodeAt(0) % colors.length;
  return colors[index];
}

function CountdownTimer({ targetTime }: { targetTime: string }) {
  const [timeLeft, setTimeLeft] = useState("");

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date();
      const target = new Date(targetTime);
      const diff = target.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeLeft("Now");
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        setTimeLeft(`${hours}h ${minutes}m`);
      } else {
        setTimeLeft(`${minutes}m`);
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [targetTime]);

  return <span className="text-xs text-[#FFC107]">{timeLeft}</span>;
}

export function ScheduledMeetings() {
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const { meetings, loading } = useMeetings(true);

  // Fallback to mock data if no meetings exist in DB yet
  const activeMeetings = meetings && meetings.length > 0 ? meetings : mockMeetings;

  const timeSlots = [
    "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", 
    "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"
  ];

  // Dynamically map date names for calendar view
  const dates = activeMeetings.map(m => m.date.split(",")[0]).filter((v, i, a) => a.indexOf(v) === i).slice(0, 3);
  const calendarDates = dates.length > 0 ? dates : ["Dec 17", "Dec 18", "Dec 19"];

  const getMeetingForSlot = (date: string, time: string) => {
    return activeMeetings.find(m => m.date.includes(date) && m.scheduledTime === time);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3 bg-white/80 backdrop-blur-xl rounded-3xl p-6 border border-gray-200/50 shadow-xl">
        <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
        <p className="text-xs text-gray-500 font-semibold">Loading synced meetings...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-amber-500/10 rounded-xl">
            <Calendar className="w-4.5 h-4.5 text-amber-600" />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-900 tracking-tight">Scheduled Meetings</h3>
            <p className="text-[11px] text-gray-500">Upcoming synced calendar syncs</p>
          </div>
        </div>
        
        {/* View toggle */}
        <div className="flex items-center gap-1 bg-gray-150/80 backdrop-blur-md rounded-xl p-1 border border-gray-200/50">
          <button
            onClick={() => setViewMode("list")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              viewMode === "list" 
                ? "bg-white text-gray-900 shadow-sm" 
                : "text-gray-500 hover:text-gray-900"
            }`}
          >
            <List className="w-3.5 h-3.5" />
            List
          </button>
          <button
            onClick={() => setViewMode("calendar")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              viewMode === "calendar" 
                ? "bg-white text-gray-900 shadow-sm" 
                : "text-gray-500 hover:text-gray-900"
            }`}
          >
            <CalendarDays className="w-3.5 h-3.5" />
            Calendar
          </button>
        </div>
      </div>

      {viewMode === "list" ? (
        <div className="space-y-3">
          {activeMeetings.map((meeting) => {
            const meetingColor = meeting.color || (meeting.priority === "high" ? "#FF9500" : meeting.priority === "medium" ? "#FFC107" : "#FFD54F");
            return (
              <div
                key={meeting.id}
                className="bg-white/70 backdrop-blur-md border border-gray-150 hover:border-amber-500/20 hover:bg-white/95 rounded-2xl p-4.5 transition-all duration-300 hover:scale-[1.01] hover:shadow-md cursor-pointer relative group"
              >
                {/* Priority dot line */}
                {meeting.priority && (
                  <div className={`absolute top-4 left-0 w-1 h-12 ${priorityDotColors[meeting.priority as "low"|"medium"|"high"] || "bg-gray-400"} rounded-r-full`}></div>
                )}
                
                <div className="flex items-start justify-between gap-4 pl-3.5">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <div 
                        className="w-2.5 h-2.5 rounded-full shrink-0 animate-pulse" 
                        style={{ backgroundColor: meetingColor }}
                      ></div>
                      <div className="text-sm font-bold text-gray-900 truncate group-hover:text-amber-600 transition-colors">
                        {meeting.title}
                      </div>
                    </div>
                    
                    {/* Attendee Avatars */}
                    <div className="flex items-center gap-2.5 mt-3 mb-2">
                      <Users className="w-4 h-4 text-gray-400 shrink-0" />
                      <div className="flex -space-x-2">
                        {meeting.attendees.slice(0, 3).map((attendee, index) => (
                          <div
                            key={index}
                            className={`w-7.5 h-7.5 rounded-full ${getAvatarColor(attendee)} flex items-center justify-center text-[10px] font-bold text-white border-2 border-white hover:z-10 transition-transform hover:scale-110`}
                            title={attendee}
                          >
                            {getInitials(attendee)}
                          </div>
                        ))}
                        {meeting.attendees.length > 3 && (
                          <div className="w-7.5 h-7.5 rounded-full bg-gray-400 flex items-center justify-center text-[10px] font-bold text-white border-2 border-white">
                            +{meeting.attendees.length - 3}
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Countdown Timer */}
                    <div className="flex items-center gap-1.5 mt-2.5">
                      <Clock className="w-3.5 h-3.5 text-amber-500" />
                      <CountdownTimer targetTime={`${meeting.date} ${meeting.scheduledTime}`} />
                    </div>
                  </div>
                  
                  <div className="flex flex-col items-end gap-2.5 shrink-0">
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium">
                      <div className="text-right leading-tight">
                        <div className="font-semibold text-gray-700">{meeting.scheduledTime}</div>
                        <div className="text-[10px] text-gray-400">{meeting.date}</div>
                        <div className="text-[10px] text-amber-600 font-bold mt-1 bg-amber-500/10 px-2 py-0.5 rounded-full inline-block">{meeting.duration}</div>
                      </div>
                    </div>
                    
                    {/* Join Meeting Button */}
                    {meeting.meetingLink && (
                      <a 
                        href={meeting.meetingLink}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-[10px] font-bold px-3 py-1.5 bg-green-500 hover:bg-green-600 rounded-full flex items-center gap-1 text-white shadow-sm shadow-green-500/15 cursor-pointer"
                      >
                        <Video className="w-3 h-3" />
                        Join
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white/80 backdrop-blur-md rounded-2xl border border-gray-150 overflow-hidden shadow-inner">
          {/* Calendar header */}
          <div className="grid grid-cols-4 border-b border-gray-150 bg-gray-50/50">
            <div className="p-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider border-r border-gray-150">Time</div>
            {calendarDates.map((date) => (
              <div key={date} className="p-3 text-[11px] font-bold text-gray-700 text-center border-r border-gray-150 last:border-r-0">
                {date}
              </div>
            ))}
          </div>
          
          {/* Calendar grid */}
          <div className="max-h-96 overflow-y-auto">
            {timeSlots.map((time) => (
              <div key={time} className="grid grid-cols-4 border-b border-gray-100 last:border-b-0">
                <div className="p-2.5 text-[10px] font-medium text-gray-400 border-r border-gray-150 bg-gray-50/20 flex items-center justify-center">
                  {time.replace(":00", "")}
                </div>
                {calendarDates.map((date) => {
                  const meeting = getMeetingForSlot(date, time);
                  const meetingColor = meeting ? (meeting.color || (meeting.priority === "high" ? "#FF9500" : meeting.priority === "medium" ? "#FFC107" : "#FFD54F")) : "";
                  return (
                    <div 
                      key={`${date}-${time}`} 
                      className="p-1 border-r border-gray-100 last:border-r-0 min-h-[65px] bg-white/30"
                    >
                      {meeting && (
                        <div 
                          className="h-full rounded-xl p-2 text-[10px] border transition-all hover:scale-[1.03] cursor-pointer shadow-sm leading-tight flex flex-col justify-between"
                          style={{ 
                            backgroundColor: `${meetingColor}18`, 
                            borderColor: `${meetingColor}45`,
                            color: meetingColor === "#FFC107" || meetingColor === "#FFB300" ? "#B7791F" : meetingColor === "#FF9500" ? "#C2410C" : "#744210"
                          }}
                        >
                          <div className="font-semibold truncate">{meeting.title}</div>
                          <div className="text-[9px] font-bold opacity-80 mt-1 flex items-center gap-0.5">
                            <Clock className="w-2.5 h-2.5" />
                            {meeting.duration}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}