/** User phrases that should open native center-panel skills (not Ops / task pipeline). */
const SKILL_CHAT =
  /\b(cam skill|camera skill|open (the )?cam(?:era)?|start (the )?cam|activate (the )?(cam|camera)(?: skill)?|use (the )?cam|turn on (the )?cam|newton'?s?\s*cradle|visualize(?: plugin)?|visuali[sz]ed skill|open (the )?visuali[sz]ation|show (me )?(a )?(chart|graph)|income projection|savings? (calculator|projection)|interactive (calculator|chart|file|tool)|calculator.*(savings?|rate|month|year)|adjust (the )?(savings|rate|amount)|(another|new|separate|create|make|build|write).{0,40}(html|page|calculator|widget)|html (file|page|calculator|tool)|close (the )?cam|close (the )?visuali[sz]ation)\b/i;

export function isSkillChatRequest(text: string): boolean {
  return SKILL_CHAT.test(text.trim());
}

const CAM_VISION =
  /\b(what (are you |do you )?see(ing)?|what('s| is) (in |on )?(the )?cam(?:era)?|describe (what you see|the scene)|what can you see|tell me what you see|camera.*see)\b/i;

export function isCamVisionQuestion(text: string): boolean {
  return CAM_VISION.test(text.trim());
}

/** Keep center workspace visible — no full Messages sheet on top. */
function isBriefingQuestion(text: string): boolean {
  const t = text.trim();
  return (
    /^\s*(?:who|what)\s+(?:is|was|are)\s+.+/i.test(t) ||
    /^\s*tell\s+me\s+about\s+.+/i.test(t) ||
    /\b(find|show)\s+(?:me\s+)?(?:a\s+)?(?:picture|photo|image)s?\s+(?:of|for)\b/i.test(t) ||
    /\b(picture|photo|image)s?\s+of\b/i.test(t) ||
    /\b(current|live)\s+price\b/i.test(t) ||
    /\b(stock|s&p|nasdaq|ticker|bitcoin)\b/i.test(t)
  );
}

export function shouldKeepWorkspaceFocus(
  text: string,
  workspaceMode: "idle" | "cam" | "visualize" | "briefing"
): boolean {
  if (workspaceMode !== "idle") return true;
  return isSkillChatRequest(text) || isCamVisionQuestion(text) || isBriefingQuestion(text);
}

/** Shown in chat while the API is working. */
export function getChatLoadingLabel(text: string): string {
  const t = text.trim();
  if (isCamVisionQuestion(t)) return "Looking at the camera";
  if (/\b(cam skill|open (the )?cam|camera skill)\b/i.test(t)) return "Opening camera";
  if (/\b(close|stop)\b.*\b(cam|camera)\b/i.test(t)) return "Closing camera";
  if (/\b(newton'?s?\s*cradle|visuali[sz]e|html|calculator|chart|graph|interactive)\b/i.test(t)) {
    return "Building visualization";
  }
  if (/\b(task|research|build me|deploy)\b/i.test(t)) return "Starting task";
  if (
    /\b(report|findings|what did (you|mark) find|summarize (the )?task|operations result)\b/i.test(
      t
    )
  ) {
    return "Reading your report";
  }
  if (/\bwhat can you do|capabilities|everything you can\b/i.test(t)) {
    return "Listing capabilities";
  }
  if (/\b(picture|photo|image)\b/i.test(t)) return "Finding images";
  if (/\b(price|stock|s&p|nasdaq|ticker)\b/i.test(t)) return "Fetching live quote";
  if (isBriefingQuestion(t)) return "Researching online";
  return "Thinking";
}
