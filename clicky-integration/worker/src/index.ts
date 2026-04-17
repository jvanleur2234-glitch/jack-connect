/**
 * Clicky Worker — Solomon OS Integration
 * Receives captures from Clicky macOS app and forwards to JackConnect Watch Once Engine
 * 
 * Routes:
 * - POST /clicky-capture — receives screen + voice from Clicky, forwards to Watch Once
 * - GET /status — health check
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // CORS for local dev
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    // Health check
    if (url.pathname === "/status") {
      return new Response(JSON.stringify({
        status: "ok",
        service: "clicky-worker-solomon",
        timestamp: new Date().toISOString()
      }), {
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    // Clicky capture webhook — receives from Clicky macOS app
    if (url.pathname === "/clicky-capture") {
      try {
        const payload = await request.json();
        
        // Extract capture data
        const screenData = payload.screen_data || payload.screenData || "";
        const voiceTranscript = payload.voice_transcript || payload.voiceTranscript || "";
        const context = payload.context || "";
        const userId = payload.user_id || payload.userId || "jack-vanleur";
        
        // Forward to local Watch Once engine
        const watchOnceUrl = env.WATCH_ONCE_URL || "http://localhost:5000/watch-once";
        
        const forwardPayload = {
          screen_data: screenData,
          voice_transcript: voiceTranscript,
          context: context,
          user_id: userId,
          source: "clicky",
          timestamp: new Date().toISOString()
        };

        // Non-blocking forward to Watch Once
        ctx.waitUntil(
          fetch(watchOnceUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(forwardPayload)
          }).catch(err => console.error("Watch Once forward failed:", err))
        );

        // Respond to Clicky immediately (don't make it wait)
        return new Response(JSON.stringify({
          success: true,
          capture_id: `clicky-${Date.now()}`,
          message: "Capture received and forwarded for processing"
        }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });

      } catch (err) {
        return new Response(JSON.stringify({
          error: "Failed to process capture",
          details: err.message
        }), {
          status: 500,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }
    }

    // Ask to automate — Clicky sends this when user says "yes automate this"
    if (url.pathname === "/ask-automate") {
      try {
        const payload = await request.json();
        const { capture_id, task_name, trigger, steps } = payload;
        
        // Create Hermes skill from this task
        const skillData = {
          name: task_name.toLowerCase().replace(/\s+/g, "-").slice(0, 50),
          trigger,
          steps,
          source_capture: capture_id,
          created_at: new Date().toISOString()
        };

        // Forward to skill creation endpoint
        const skillCreationUrl = env.SKILL_CREATE_URL || "http://localhost:5000/create-skill";
        
        ctx.waitUntil(
          fetch(skillCreationUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(skillData)
          }).catch(err => console.error("Skill creation failed:", err))
        );

        return new Response(JSON.stringify({
          success: true,
          skill_created: skillData.name,
          message: "Skill is being created. Russell Tuna will now do this automatically."
        }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });

      } catch (err) {
        return new Response(JSON.stringify({
          error: "Failed to create skill",
          details: err.message
        }), {
          status: 500,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }
    }

    // Not found
    return new Response(JSON.stringify({
      error: "Not found",
      available_routes: ["/status", "/clicky-capture", "/ask-automate"]
    }), {
      status: 404,
      headers: { "Content-Type": "application/json", ...corsHeaders }
    });
  }
};