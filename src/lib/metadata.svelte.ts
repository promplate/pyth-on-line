export const defaultMetadata = {
  ogTitle: "Python Online",
  ogDescription: "A simple online python console",
};

export class Metadata {
  ogTitle = $state(defaultMetadata.ogTitle);
  ogDescription = $state(defaultMetadata.ogDescription);
}
