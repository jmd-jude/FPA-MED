/**
 * Search Cases API route - proxies to backend
 */

export async function POST(request: Request) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  try {
    const body = await request.json();

    const response = await fetch(`${backendUrl}/search-cases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    return Response.json(data, { status: response.status });
  } catch (error) {
    return Response.json(
      { error: 'Failed to connect to backend' },
      { status: 503 }
    );
  }
}
