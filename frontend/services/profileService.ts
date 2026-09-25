import { http } from "./httpClient";
import type { CareerProfile } from "@/types";

export async function getProfile(): Promise<CareerProfile> {
  return http.get<CareerProfile>("/profile");
}

export async function uploadResume(file: File): Promise<{ message: string; profile: Partial<CareerProfile> }> {
  const form = new FormData();
  form.append("file", file);
  return http.postForm("/resume", form);
}
