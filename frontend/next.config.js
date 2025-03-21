/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // Set the ROOT_DIR to the parent directory for executing the Python command
    ROOT_DIR: process.cwd().replace('/frontend', '')
  },
  // Increase timeout for chunk loading
  onDemandEntries: {
    // period (in ms) where the server will keep pages in the buffer
    maxInactiveAge: 120 * 1000,
    // number of pages that should be kept simultaneously without being disposed
    pagesBufferLength: 5,
  },
  // Remove experimental appDir since it's now the default in Next.js 13+
  reactStrictMode: true,
  swcMinify: true,
}

module.exports = nextConfig 