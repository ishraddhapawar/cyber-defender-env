FROM python:3.11-slim

# Create standard user for HF spaces
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirement details
# Since we don't have a requirements.txt physically separated, 
# we'll install globally in the users space
RUN pip install --no-cache-dir fastapi uvicorn pydantic requests openai

# Copy source code with owner privileges
COPY --chown=user . .

# Expose HF required port
EXPOSE 7860

# Command to run uvicorn on port 7860 natively
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
