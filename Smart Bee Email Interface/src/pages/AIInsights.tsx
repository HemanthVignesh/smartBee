import { useEffect, useState } from "react";
import { fetchInsights } from "@/lib/api";
import { Insight } from "@/types/insight";

export default function AIInsights() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInsights()
      .then(setInsights)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading insights...</div>;

  return (
    <div className="space-y-4">
      {insights.map((item) => (
        <div
          key={item.email_id}
          className="rounded-lg border p-4 shadow-sm"
        >
          <h3 className="font-semibold">{item.intent}</h3>
          <p className="text-sm text-gray-600">{item.summary}</p>

          <div className="mt-2 flex gap-2">
            <span className="text-xs bg-red-100 px-2 py-1 rounded">
              {item.priority}
            </span>
            <span className="text-xs bg-blue-100 px-2 py-1 rounded">
              {Math.round(item.confidence * 100)}% confident
            </span>
          </div>

          <div className="mt-3 space-y-2">
            {item.actions.map((action) => (
              <button
                key={action.action_id}
                className="px-3 py-1 text-sm border rounded hover:bg-gray-100"
              >
                {action.action_type.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
