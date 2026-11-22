export default {
  fetch(request: Request): Response {
    const { pathname } = new URL(request.url);
    return Response.json(
      { error: `No such endpoint: ${pathname}` },
      { status: 404 },
    );
  },
};
