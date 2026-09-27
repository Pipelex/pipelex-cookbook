/**
 * What the form accepts, shared by the page and its server action, which checks it again since anyone can post to it.
 * Every record is written by its own model call on your key, and the method takes its count as a plain number that
 * nothing bounds, so the action refuses a count that is not a whole number within this range.
 */
export const MAX_RECORDS = 20;
export const MAX_DESCRIPTION_LENGTH = 4_000;
