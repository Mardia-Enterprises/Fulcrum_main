/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // Set the ROOT_DIR to the parent directory for executing the Python command
    ROOT_DIR: process.cwd().replace('/frontend', '')
  },
  // Use the App Router
  experimental: {
    appDir: true,
  },
  // Enable server components
  reactStrictMode: true,
  swcMinify: true,
}

module.exports = nextConfig 