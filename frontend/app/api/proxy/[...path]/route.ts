import { NextRequest, NextResponse } from 'next/server';
import config from '../../../config';

const API_BASE_URL = config.apiUrl;

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const url = `${API_BASE_URL}/${path}${request.nextUrl.search}`;

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error(`Error proxying GET request to ${url}:`, error);
    return NextResponse.json(
      { error: 'Failed to proxy request', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const url = `${API_BASE_URL}/${path}`;

  try {
    const body = await request.json();
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error(`Error proxying POST request to ${url}:`, error);
    return NextResponse.json(
      { error: 'Failed to proxy request', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
} 