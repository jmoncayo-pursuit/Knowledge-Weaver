"""
Clip 3 Playwright Video Demo
=============================
This script uses Playwright to automate and VIDEO RECORD
the Bridge the Gap workflow, proving DOM accessibility.

SETUP:
  pip install playwright
  playwright install chromium

RUN:
  python demos/clip3_playwright_video.py

OUTPUT:
  demos/recordings/clip3_demo.webm
"""

import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    # Ensure recordings directory exists
    recordings_dir = os.path.join(os.path.dirname(__file__), "recordings")
    os.makedirs(recordings_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser with video recording
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            record_video_dir=recordings_dir,
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        
        print("🎬 Starting Clip 3 Demo Recording...")
        print("="*50)
        
        # Step 1: Navigate to dashboard
        print("Step 1: Navigating to dashboard...")
        await page.goto("http://localhost:8080")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        print("  ✓ Dashboard loaded")
        
        # Step 2: Scroll to Bridge the Gap section
        print("Step 2: Scrolling to Bridge the Gap...")
        gap_section = page.locator("text=Bridge the Gap")
        await gap_section.scroll_into_view_if_needed()
        await asyncio.sleep(1)
        print("  ✓ Section visible")
        
        # Step 3: Click on a knowledge gap
        print("Step 3: Selecting a knowledge gap...")
        # Try to find our demo gap or first available
        gap_item = page.locator(".gap-item").first
        await gap_item.click()
        await asyncio.sleep(1)
        print("  ✓ Gap selected")
        
        # Step 4: Type the answer
        print("Step 4: Typing answer...")
        answer_textarea = page.locator("#answer-content")
        await answer_textarea.fill(
            "Navigate to the Benefits portal:\n"
            "1. Go to Benefits > Dependents\n"
            "2. Click 'Add New Dependent'\n"
            "3. Upload required documentation\n"
            "4. Submit within 31 days of QLE"
        )
        await asyncio.sleep(1)
        print("  ✓ Answer typed")
        
        # Step 5: Submit the answer
        print("Step 5: Submitting answer...")
        submit_btn = page.locator('[data-testid="submit-answer-btn"]')
        await submit_btn.click()
        await asyncio.sleep(3)
        print("  ✓ Answer submitted")
        
        # Step 6: Scroll to see result
        print("Step 6: Viewing result in knowledge table...")
        table = page.locator("#knowledge-table-body")
        await table.scroll_into_view_if_needed()
        await asyncio.sleep(2)
        print("  ✓ Result visible")
        
        # Take final screenshot
        screenshot_path = os.path.join(recordings_dir, "clip3_final.png")
        await page.screenshot(path=screenshot_path)
        print(f"  📸 Screenshot saved: {screenshot_path}")
        
        # Close and save video
        await context.close()
        await browser.close()
        
        print("="*50)
        print("🎉 Demo Complete!")
        print(f"📹 Video saved to: {recordings_dir}/")
        print("\nThis proves DOM-level robot accessibility!")

if __name__ == "__main__":
    asyncio.run(main())
