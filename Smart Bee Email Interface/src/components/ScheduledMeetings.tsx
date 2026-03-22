import { Calendar, Clock, Users, List, CalendarDays, Video } from "lucide-react";
import { useState, useEffect } from "react";

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

  const timeSlots = [
    "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", 
    "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"
  ];

  const dates = ["Dec 17", "Dec 18", "Dec 19"];

  const getMeetingForSlot = (date: string, time: string) => {
    return mockMeetings.find(m => m.date.includes(date) && m.scheduledTime === time);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          <h2>Scheduled Meetings</h2>
        </div>
        
        {/* View toggle */}
        <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode("list")}
            className={`px-3 py-1.5 rounded-md text-xs flex items-center gap-1.5 transition-all ${
              viewMode === "list" 
                ? "bg-white text-gray-900 shadow-sm" 
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <List className="w-3.5 h-3.5" />
            List
          </button>
          <button
            onClick={() => setViewMode("calendar")}
            className={`px-3 py-1.5 rounded-md text-xs flex items-center gap-1.5 transition-all ${
              viewMode === "calendar" 
                ? "bg-white text-gray-900 shadow-sm" 
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <CalendarDays className="w-3.5 h-3.5" />
            Calendar
          </button>
        </div>
      </div>

      {viewMode === "list" ? (
        <div className="space-y-2">
          {mockMeetings.map((meeting) => (
            <div
              key={meeting.id}
              className="bg-white border border-gray-200 rounded-xl p-4 hover:border-[#FFC107] hover:shadow-lg transition-all duration-300 hover:-translate-y-1 relative group"
            >
              {/* Priority dot */}
              {meeting.priority && (
                <div className={`absolute top-4 left-0 w-1 h-12 ${priorityDotColors[meeting.priority]} rounded-r`}></div>
              )}
              
              <div className="flex items-start justify-between gap-4 pl-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <div 
                      className="w-3 h-3 rounded-full shrink-0" 
                      style={{ backgroundColor: meeting.color }}
                    ></div>
                    <div className="text-gray-900 truncate">{meeting.title}</div>
                  </div>
                  
                  {/* Attendee Avatars */}
                  <div className="flex items-center gap-2 mt-3 mb-2">
                    <Users className="w-4 h-4 text-gray-500" />
                    <div className="flex -space-x-2">
                      {meeting.attendees.slice(0, 3).map((attendee, index) => (
                        <div
                          key={index}
                          className={`w-8 h-8 rounded-full ${getAvatarColor(attendee)} flex items-center justify-center text-xs text-white border-2 border-white hover:z-10 transition-transform hover:scale-110`}
                          title={attendee}
                        >
                          {getInitials(attendee)}
                        </div>
                      ))}
                      {meeting.attendees.length > 3 && (
                        <div className="w-8 h-8 rounded-full bg-gray-400 flex items-center justify-center text-xs text-white border-2 border-white">
                          +{meeting.attendees.length - 3}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Countdown Timer */}
                  <div className="flex items-center gap-2 mt-2">
                    <Clock className="w-4 h-4 text-[#FFC107]" />
                    <CountdownTimer targetTime={`${meeting.date} ${meeting.scheduledTime}`} />
                  </div>
                </div>
                
                <div className="flex flex-col items-end gap-2">
                  <div className="flex items-center gap-2 text-sm text-gray-600 shrink-0">
                    <div className="text-right">
                      <div>{meeting.scheduledTime}</div>
                      <div className="text-xs text-gray-400">{meeting.date}</div>
                      <div className="text-xs text-[#FFC107] mt-1">{meeting.duration}</div>
                    </div>
                  </div>
                  
                  {/* Join Meeting Button */}
                  {meeting.meetingLink && (
                    <button className="opacity-0 group-hover:opacity-100 transition-opacity text-xs px-3 py-1.5 bg-green-500 hover:bg-green-600 rounded-lg flex items-center gap-1 text-white">
                      <Video className="w-3 h-3" />
                      Join Meeting
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {/* Calendar header */}
          <div className="grid grid-cols-4 border-b border-gray-200 bg-gray-50">
            <div className="p-2 text-xs text-gray-600 border-r border-gray-200">Time</div>
            {dates.map((date) => (
              <div key={date} className="p-2 text-xs text-gray-900 text-center border-r border-gray-200 last:border-r-0">
                {date}
              </div>
            ))}
          </div>
          
          {/* Calendar grid */}
          <div className="max-h-96 overflow-y-auto">
            {timeSlots.map((time) => (
              <div key={time} className="grid grid-cols-4 border-b border-gray-200 last:border-b-0">
                <div className="p-2 text-xs text-gray-500 border-r border-gray-200 bg-gray-50/50">
                  {time}
                </div>
                {dates.map((date) => {
                  const meeting = getMeetingForSlot(date, time);
                  return (
                    <div 
                      key={`${date}-${time}`} 
                      className="p-1 border-r border-gray-200 last:border-r-0 min-h-[60px]"
                    >
                      {meeting && (
                        <div 
                          className="h-full rounded-md p-2 text-xs text-white transition-all hover:scale-105 cursor-pointer"
                          style={{ backgroundColor: meeting.color }}
                        >
                          <div className="line-clamp-2">{meeting.title}</div>
                          <div className="text-xs opacity-90 mt-1">{meeting.duration}</div>
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