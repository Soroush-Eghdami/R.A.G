import { useQuery } from "@tanstack/react-query";
import { getHealth, getModels } from "../api/client";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
  });
}

export function useModels() {
  return useQuery({
    queryKey: ["models"],
    queryFn: () => getModels(),
    staleTime: 30_000,
    retry: 0,
  });
}
