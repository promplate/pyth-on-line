// PEP 508: name [extras] versionspec ; marker
export function parseDep(depStr: string) {
  const [specPart, ...markerParts] = depStr.split(";");
  const marker = markerParts.length > 0 ? markerParts.join(";").trim() : "";
  const specTrimmed = specPart.trim();
  const nameMatch = specTrimmed.match(/^([a-z\d][-\w.]*[a-z\d]|[a-z\d])/i);
  if (!nameMatch)
    return { name: "", extras: "", versionspec: "", marker };
  const name = nameMatch[1];
  const afterName = specTrimmed.slice(name.length).trim();
  let extras = "";
  let afterExtras = afterName;
  if (afterName.startsWith("[")) {
    const extrasMatch = afterName.match(/^\[([^\]]*)\]/);
    if (extrasMatch) {
      extras = extrasMatch[0];
      afterExtras = afterName.slice(extrasMatch[0].length).trim();
    }
  }
  return { name, extras, versionspec: afterExtras, marker };
}

export function getOperatorClass(spec: string) {
  if (spec.includes("~="))
    return "compatible-release";
  if (spec.includes("==="))
    return "arbitrary-equality";
  if (spec.includes("=="))
    return "version-matching";
  if (spec.includes("!="))
    return "version-exclusion";
  if (spec.includes(">=") || spec.includes("<="))
    return "inclusive-ordered";
  if (spec.includes(">") || spec.includes("<"))
    return "exclusive-ordered";
  return "version-other";
}
