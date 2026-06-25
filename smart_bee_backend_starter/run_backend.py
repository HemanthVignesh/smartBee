# run_backend.py
import importlib.metadata

class MockEntryPoints(tuple):
    def select(self, *args, **kwargs):
        return MockEntryPoints()

importlib.metadata.distributions = lambda *args, **kwargs: []
importlib.metadata.entry_points = lambda *args, **kwargs: MockEntryPoints()

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
