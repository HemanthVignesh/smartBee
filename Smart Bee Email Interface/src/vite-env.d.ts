/// <reference types="vite/client" />

declare module "*.png" {
  const value: string;
  return value;
}

declare module "*.jpg" {
  const value: string;
  return value;
}

declare module "*.svg" {
  const content: any;
  export default content;
}
