import { handle } from "../lib/auth.js";

// Проверка входа перед каждым запросом к сайту (см. ../lib/auth.js).
export const onRequest = (context) =>
  handle(context.request, context.env, context.next, (p) => context.waitUntil(p));
