import fitz
import Vision
import Quartz
import json
import time
import os

pdf_path = 'data/raw_pdfs/electricity_act_2023.pdf'
out_ocr_path = 'data/raw_pdfs/electricity_act_2023_ocr.json'

doc = fitz.open(pdf_path)
total_pages = len(doc)
print(f'Starting Apple Vision OCR on {pdf_path} ({total_pages} pages)...')

request = Vision.VNRecognizeTextRequest.alloc().init()
request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
request.setUsesLanguageCorrection_(True)

start_time = time.time()
pages_data = []

for p_idx in range(total_pages):
    page = doc[p_idx]
    pix = page.get_pixmap(dpi=200)
    img_bytes = pix.tobytes('png')
    data = Quartz.CFDataCreate(None, img_bytes, len(img_bytes))
    provider = Quartz.CGDataProviderCreateWithCFData(data)
    cg_image = Quartz.CGImageCreateWithPNGDataProvider(provider, None, False, Quartz.kCGRenderingIntentDefault)
    
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
    handler.performRequests_error_([request], None)
    
    results = request.results()
    page_obs = []
    for obs in results:
        top = obs.topCandidates_(1)[0].string().strip()
        box = obs.boundingBox()
        page_obs.append({
            'text': top,
            'x': float(box.origin.x),
            'y': float(box.origin.y),
            'w': float(box.size.width),
            'h': float(box.size.height)
        })
    pages_data.append(page_obs)
    if (p_idx + 1) % 20 == 0 or (p_idx + 1) == total_pages:
        elapsed = time.time() - start_time
        print(f'Processed {p_idx + 1}/{total_pages} pages ({elapsed:.1f}s)...')

with open(out_ocr_path, 'w') as f:
    json.dump(pages_data, f, indent=2)

print(f'Finished OCR in {time.time() - start_time:.1f}s. Saved to {out_ocr_path}')
