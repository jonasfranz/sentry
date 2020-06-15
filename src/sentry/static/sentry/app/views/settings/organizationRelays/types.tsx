export type Relay = {
  publicKey: string;
  name: string;
  created: string;
  firstUsed: string;
  lastUsed: string | null;
  lastModified?: string;
  description?: string;
};
