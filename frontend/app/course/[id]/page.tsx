"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { createClient } from "@/lib/supabaseClient";

export default function CoursePage() {
  const { id } = useParams<{ id: string }>();
  const supabase = createClient();
  const [course, setCourse] = useState<any>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const load = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        setError("Not logged in.");
        return;
      }

      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/courses/${id}`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (!res.ok) {
          const err = await res.json();
          setError(err.detail || "Failed to load course.");
          return;
        }
        setCourse(await res.json());
      } catch {
        setError("Could not reach backend.");
      }
    };
    load();
  }, [id]);

  if (error) return <main className="mx-auto max-w-2xl p-8 text-red-600">{error}</main>;
  if (!course) return <main className="mx-auto max-w-2xl p-8">Loading course...</main>;

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">{course.title}</h1>
      <p className="mt-2 text-neutral-600">{course.description}</p>

      <div className="mt-4 flex gap-4 text-sm text-neutral-500">
        <span>Level: {course.difficulty_level}</span>
        <span>~{course.estimated_time_minutes} min</span>
      </div>

      {course.learning_objectives?.length > 0 && (
        <div className="mt-6">
          <h2 className="font-medium">Learning Objectives</h2>
          <ul className="list-disc pl-5 text-sm text-neutral-600">
            {course.learning_objectives.map((o: string, i: number) => (
              <li key={i}>{o}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-8 space-y-6">
        {course.chapters.map((chapter: any) => (
          <div key={chapter.id} className="rounded-lg border p-4">
            <h3 className="text-lg font-semibold">{chapter.title}</h3>
            <p className="mt-1 text-sm text-neutral-500">{chapter.summary}</p>

            <div className="mt-4 space-y-4">
              {chapter.lessons.map((lesson: any) => (
                <div key={lesson.id} className="border-t pt-4">
                  <h4 className="font-medium">{lesson.title}</h4>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-neutral-700">
                    {lesson.content_markdown}
                  </p>
                  {lesson.key_takeaways?.length > 0 && (
                    <div className="mt-2 text-sm">
                      <strong>Key takeaways:</strong>
                      <ul className="list-disc pl-5 text-neutral-600">
                        {lesson.key_takeaways.map((k: string, i: number) => (
                          <li key={i}>{k}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
