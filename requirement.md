Khách có 10 công ty:
	Slabx 
	Promax kitchen refacing
	NuGuard windows and doors
	Luxview blinds
	Xwall painting 
	Durham Reno hub 
	Lifetime flooring
	Vista closets
	Oneday roofing 
	Panex showe glass

Tôi cần tạo video 30s, tôi đã có sẵn CTA dài 6s. tôi cần tạo 3 video 24s bằng veo3 và ghép lại với nhau. tôi sẽ ghép CTA vô sau.
Bố cục video sẽ bao gồm: Hook, content, CTA.
Yêu cầu của khách:
	Quality standards: Clean footage, readable text, no clutter
		Video phải sạch, hình ảnh rõ.
		Text dễ đọc.
		Không nhồi quá nhiều text/element khiến video rối.

Hãy tạo cho tôi 1 hệ thống python có api để tôi gọi từ n8n.

api tên là /generate-video/
input tôi sẽ truyền vào gồm:
openai_api_key
geminigen_api_key
model (default = veo-3.1)
resolution (default = 1080p)
aspect_ratio (default = 9:16)
duration (default = 8)
company_information (gồm 1 loạt dữ liệu của cty), b có thể bỏ qua CTA Video Link, Logo File, Booking or quote links, Address, Phone Number, Background Music, row_number, vì chúng ko giúp ích gì khi tạo video. hãy code để loại chúng ra khi nhận đc input này.
VD về company_information:
[
  {
    "row_number": 2,
    "Company Name": "SlabX Kitchens & Countertops",
    "Video and Image Style": "Premium, design-led, confident, experienced",
    "Avoid": "Hard-sell language, discount shouting",
    "Background Music": "https://drive.google.com/drive/folders/1ESvtj1Sws_N_dsjd_dY1JvTrIXFaylIy?usp=drive_link",
    "Content Pillars": "Project showcase, material close-ups, referral program",
    "Phone Number": 9055053003,
    "Address": "222 Bond St W, Oshawa ON",
    "Color": "#373737 #7FC143 #000000 #D8DDD7 #FFFFFF",
    "Fonts": "Roboto, Literaturnaya",
    "Website Content (service/product pages, About text, FAQs)": "Website Content\n\nAbout: slabX works with a hand-selected team of designers and master craftsmen so every phase, from the first quote to the final installation, reflects precision, care and dedication. The company aims to be great, not just good, and believes every detail matters.\n\nFine Cabinetry: Custom cabinetry for residential and commercial clients, including kitchen cabinets, vanities, closets, mudroom lockers and bookshelves, designed and built to fit your space and style.\n\nCustom Millwork: Specialized woodworking beyond typical trim carpentry, including wall paneling, fireplace mantels, floating shelves and decorative moldings.\n\nCabinet Door Profiles: A range of painted cabinet door profiles that can be painted in any colour to match your decor.\n\nSinks: A Bosco sink collection built for busy kitchens, filterable by series, mount style, material (including copper, stainless and granite) and number of basins.\n\nShowrooms: Oshawa (222 Bond St W, 905-505-3003) and Barrie (322 King St, Unit 8, 705-708-4000).\n\nShort Company Description\n\nslabX is a countertop and custom cabinetry specialist with showrooms in Oshawa and Barrie. A team of designers and master craftsmen handles every project from quote to installation.\n\nServices List\n\nCountertops, custom cabinets, bathroom vanities, full kitchen renovations, fine cabinetry (kitchens, vanities, closets, mudroom lockers, bookshelves), custom millwork (wall paneling, fireplace mantels, floating shelves, decorative moldings), painted cabinet doors, Bosco sinks",
    "Short Company Description": "Durham Region's countertop specialists, with over a decade of experience and multiple showrooms. Quartz, porcelain and more, with expert help choosing your slab.",
    "Services List": "Quartz and porcelain countertops, kitchen cabinetry, cabinet refacing, full kitchen renovations, sinks and backsplashes",
    "Service Area (Durham Region and the GTA)": "Durham Region and the GTA",
    "Logo File": "https://drive.google.com/file/d/1TpyySFI8pbXm7A2A5fJiG1v54LxoaMHS/view?usp=drive_link",
    "Booking or quote links": "https://www.slabx.ca/oshawa",
    "CTA Video Link": "https://drive.google.com/file/d/1bhpjgR7eQY0YxrGTGswOhOTHKqFm7CWk/view?usp=drivesdk"
  }
]
before_images_path (1 loạt ảnh before)
during_images_path (1 loạt ảnh during)
after_images_path (1 loạt ảnh after)
VD về 3 images_path:
[
  {
    [
      "/tmp/1vJCbfUCgqiilPyJNq4Tp-cmCDf9Roh4U.jpg",
      "/tmp/1vJCbfUCgqiilPyJNq4Tp-cmCDf9Roh4U.jpg",
      "/tmp/1vJCbfUCgqiilPyJNq4Tp-cmCDf9Roh4U.jpg",
      "/tmp/1vJCbfUCgqiilPyJNq4Tp-cmCDf9Roh4U.jpg",
      "/tmp/1vJCbfUCgqiilPyJNq4Tp-cmCDf9Roh4U.jpg"
    ]
  }
]

các images_path có thể rỗng hoặc không truyền vào.

output tôi expect là output video path (24s)

Hãy dùng api sau để tạo video qua veo3 (tôi paste vô node của n8n, bạn hãy phân tích để lấy ra đc api kèm header và payload nhé):
{
  "nodes": [
    {
      "parameters": {
        "method": "POST",
        "url": "https://api.geminigen.ai/uapi/v1/video-gen/veo",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "x-api-key",
              "value": "={{ $('Config').first().json.geminigen.key }}"
            }
          ]
        },
        "sendBody": true,
        "contentType": "multipart-form-data",
        "bodyParameters": {
          "parameters": [
            {
              "name": "prompt",
              "value": "={{ $('Create Prompt to Generate CTA').first().json.text }}"
            },
            {
              "name": "model",
              "value": "veo-3.1"
            },
            {
              "name": "resolution",
              "value": "1080p"
            },
            {
              "name": "aspect_ratio",
              "value": "9:16"
            },
            {
              "name": "duration",
              "value": "6"
            },
            {
              "name": "ref_images"
            }
          ]
        },
        "options": {
          "redirect": {
            "redirect": {}
          }
        }
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.3,
      "position": [
        -8912,
        1632
      ],
      "id": "53683e61-efeb-490b-b6c2-245092013679",
      "name": "Create CTA Video1",
      "retryOnFail": true,
      "onError": "continueErrorOutput"
    }
  ],
  "connections": {},
  "pinData": {},
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "be74c41cbfbff63aa71a769a5c5130a6f8d177cd514aafd727221819ff15ab68"
  }
}

Hãy dùng API sau để check quá trình tạo video của geminigen (tôi paste vô node của n8n, bạn hãy phân tích để lấy ra đc api kèm header và payload và logic check nhé):
{
  "nodes": [
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "strict",
            "version": 2
          },
          "conditions": [
            {
              "id": "47d6fbf1-c426-49b5-b83a-3e62249fcb4f",
              "leftValue": "={{ $json.status }}",
              "rightValue": 2,
              "operator": {
                "type": "number",
                "operation": "equals"
              }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "type": "n8n-nodes-base.if",
      "typeVersion": 2.2,
      "position": [
        -8496,
        1072
      ],
      "id": "dfaf6464-fbb2-4f21-bc66-91ab521d41f9",
      "name": "If success3"
    },
    {
      "parameters": {
        "amount": 30
      },
      "type": "n8n-nodes-base.wait",
      "typeVersion": 1.1,
      "position": [
        -8496,
        1344
      ],
      "id": "cd7fbe55-fd4c-479f-b906-f8bb9f8c174e",
      "name": "Wait3",
      "webhookId": "fef71b1f-f367-4b42-a68a-bc0bd57b0fb5"
    },
    {
      "parameters": {
        "url": "=https://api.geminigen.ai/uapi/v1/history/{{ $json.uuid }}",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "x-api-key",
              "value": "={{ $('Config').first().json.geminigen.key }}"
            }
          ]
        },
        "options": {
          "redirect": {
            "redirect": {}
          }
        }
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.3,
      "position": [
        -8704,
        1072
      ],
      "id": "a7cb6eea-929c-4c72-93d7-4c3983e64693",
      "name": "Check Result from GeminiGen3",
      "retryOnFail": true,
      "onError": "continueErrorOutput"
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "strict",
            "version": 2
          },
          "conditions": [
            {
              "id": "3097977f-65c7-40cf-8e4f-eb332dd79b92",
              "leftValue": "={{ $json.status }}",
              "rightValue": 3,
              "operator": {
                "type": "number",
                "operation": "equals"
              }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "type": "n8n-nodes-base.if",
      "typeVersion": 2.2,
      "position": [
        -8704,
        1344
      ],
      "id": "b60ea7e8-f980-4c39-9eb6-225898877e31",
      "name": "If failed3"
    }
  ],
  "connections": {
    "If success3": {
      "main": [
        [],
        [
          {
            "node": "If failed3",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Wait3": {
      "main": [
        [
          {
            "node": "Check Result from GeminiGen3",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Check Result from GeminiGen3": {
      "main": [
        [
          {
            "node": "If success3",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "If failed3": {
      "main": [
        [],
        [
          {
            "node": "Wait3",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "pinData": {},
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "be74c41cbfbff63aa71a769a5c5130a6f8d177cd514aafd727221819ff15ab68"
  }
}

tôi expect trong API /generate-video/, bạn có thể phân tích các dữ liệu trên để tạo ý tưởng, tạo prompt và tạo video sao cho hợp lý.
hãy dùng openai để tạo prompt.
về 3 images_path, bạn có thể không cần phân tích, hoặc nếu cần phân tích, hãy gọi api openai để phân tích.

dưới đây là payload mẫu, hãy sử dụng nó để thiết kế API:
{
  "openai_api_key": "sk-",
  "geminigen_api_key": "geminiai-",
  "imgbb_api_key": "",
  "model": "veo-3.1",
  "resolution": "1080p",
  "aspect_ratio": "9:16",
  "duration": 8,
  "company_information": [{"json":{"row_number":2,"Company Name":"SlabX Kitchens & Countertops","Video and Image Style":"Premium, design-led, confident, experienced","Avoid":"Hard-sell language, discount shouting","Background Music":"https://drive.google.com/drive/folders/1ESvtj1Sws_N_dsjd_dY1JvTrIXFaylIy?usp=drive_link","Content Pillars":"Project showcase, material close-ups, referral program","Phone Number":9055053003,"Address":"222 Bond St W, Oshawa ON","Color":"#373737 #7FC143 #000000 #D8DDD7 #FFFFFF","Fonts":"Roboto, Literaturnaya","Website Content (service/product pages, About text, FAQs)":"Website Content\n\nAbout: slabX works with a hand-selected team of designers and master craftsmen so every phase, from the first quote to the final installation, reflects precision, care and dedication. The company aims to be great, not just good, and believes every detail matters.\n\nFine Cabinetry: Custom cabinetry for residential and commercial clients, including kitchen cabinets, vanities, closets, mudroom lockers and bookshelves, designed and built to fit your space and style.\n\nCustom Millwork: Specialized woodworking beyond typical trim carpentry, including wall paneling, fireplace mantels, floating shelves and decorative moldings.\n\nCabinet Door Profiles: A range of painted cabinet door profiles that can be painted in any colour to match your decor.\n\nSinks: A Bosco sink collection built for busy kitchens, filterable by series, mount style, material (including copper, stainless and granite) and number of basins.\n\nShowrooms: Oshawa (222 Bond St W, 905-505-3003) and Barrie (322 King St, Unit 8, 705-708-4000).\n\nShort Company Description\n\nslabX is a countertop and custom cabinetry specialist with showrooms in Oshawa and Barrie. A team of designers and master craftsmen handles every project from quote to installation.\n\nServices List\n\nCountertops, custom cabinets, bathroom vanities, full kitchen renovations, fine cabinetry (kitchens, vanities, closets, mudroom lockers, bookshelves), custom millwork (wall paneling, fireplace mantels, floating shelves, decorative moldings), painted cabinet doors, Bosco sinks","Short Company Description":"Durham Region's countertop specialists, with over a decade of experience and multiple showrooms. Quartz, porcelain and more, with expert help choosing your slab.","Services List":"Quartz and porcelain countertops, kitchen cabinetry, cabinet refacing, full kitchen renovations, sinks and backsplashes","Service Area (Durham Region and the GTA)":"Durham Region and the GTA","Logo File":"https://drive.google.com/file/d/1TpyySFI8pbXm7A2A5fJiG1v54LxoaMHS/view?usp=drive_link","Booking or quote links":"https://www.slabx.ca/oshawa","CTA Video Link":"https://drive.google.com/file/d/1bhpjgR7eQY0YxrGTGswOhOTHKqFm7CWk/view?usp=drivesdk"},"pairedItem":{"item":0}}],
  "before_images_path": "/tmp/1vJCbfUCgqiilPyJNq4Tp-cmCDf9Roh4U.jpg,/tmp/1dcXT0Bw1S8hxaghTjkRZNcp5eNixWI45.jpg,/tmp/10kEto1MRSLVL25inVT4Vhrled_i-fQP8.jpg,/tmp/1ST3yI4H898rp9VZfFo4gzBTAvvA4FYJn.jpg,/tmp/1I-BHyuLyTsapwBk7qy2ECLGJq_qO0U7Q.jpg",
  "during_images_path": "/tmp/1FKUCDl0C0XUjVnpN7B3AaQay2t7hx-bz.jpg,/tmp/15-IWYQC_uoy3W70PfgAzBrEHNffSZm9Z.jpg,/tmp/1rEAv6uQzjWx7IwCT6_m80PWQfvAektv4.jpg,/tmp/1s0vJ_BW3TgCPq__Md25RtZgx_7TRFS0z.jpg,/tmp/190V4iOstnkAagAtvm6BPUZuFghVDBEMz.jpg,/tmp/1VITIleTlxprsdOBXiFUS9x-YQdg8xsMq.jpg,/tmp/1xCx6TW9Oget_uU9VfDljMArCx5dTU_T8.jpg,/tmp/1SIsGozSIgd3jp2Lb58zjbxBu3HKw0UMX.jpg,/tmp/1wkFPiZWk6rBrOmLL8E4_vJEPNGgtJw9m.jpg",
  "after_images_path": "/tmp/1FW6HJjcPdlAM1reRDu18UFloVtM0sggr.jpg,/tmp/19HXZx5DdppTqJ-Lhr-DUCpQwjhboF2LR.jpg,/tmp/1Y6HApQ939ULwcpxhjyVLz1AABHK3PXsD.jpg,/tmp/1gN6Fz5Sg00Nw23r9HjJYrz02q5ljR6gP.jpg,/tmp/1kHjOUpRZhQfFcseJ2GKsPyH_8Gz_lPpJ.jpg,/tmp/1iHm4IqmeTFzaV62uaY-WtvEtZSSXeuoW.jpg"
}

Vì geminigen.ai chỉ chấp nhận link ảnh truyền vào khi ở imgbb link, nên khi bạn cần sử dụng ảnh để đẩy lên geminigen.ai API, bạn hãy upload ảnh từ local lên imgbb thông qua API của họ như sau:
curl --location 'https://api.imgbb.com/1/upload?expiration=60000&key=c9996d4ada59b1a514a5b14c9765c59e' \
--form 'image=@"postman-cloud:///1f0f82c7-bad9-4bb0-82b7-028e4c369338"'

với API trên, key chính là imgbb_api_key mà tôi truyền vào qua API /generate-video/ nhé

đây là output mẫu của API imgbb:
{
    "data": {
        "id": "N2d2Kw9d",
        "title": "áo mẫu test",
        "url_viewer": "https://ibb.co/N2d2Kw9d",
        "url": "https://i.ibb.co/3m9mctp9/o-m-u-test.png",
        "display_url": "https://i.ibb.co/3m9mctp9/o-m-u-test.png",
        "width": 409,
        "height": 514,
        "size": 235357,
        "time": 1792139711,
        "expiration": 6000,
        "image": {
            "filename": "o-m-u-test.png",
            "name": "o-m-u-test",
            "mime": "image/png",
            "extension": "png",
            "url": "https://i.ibb.co/3m9mctp9/o-m-u-test.png"
        },
        "thumb": {
            "filename": "o-m-u-test.png",
            "name": "o-m-u-test",
            "mime": "image/png",
            "extension": "png",
            "url": "https://i.ibb.co/N2d2Kw9d/o-m-u-test.png"
        },
        "delete_url": "https://ibb.co/N2d2Kw9d/b6f1fab893791101c5416474d64c3967"
    },
    "success": true,
    "status": 200
}