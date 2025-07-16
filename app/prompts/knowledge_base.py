def website_info_prompt():
    prompt = """Task:
You will be given the link to a company's official website. Your job is to scrape the site's content (excluding source code and design elements) and generate a comprehensive, human-like narrative (1000-2000 words) that provides an in-depth overview of the business.

What to Extract and Cover:
   Your output should be a well-structured article covering the following:

   Company Overview

   Name of the business

   Year founded

   Headquarters or location

   Mission or vision statement

   General background and context (why it was founded, the problem it solves)

   Founders & Team

   Names and roles of founders or key team members

   Short bios or background info

   Any notable achievements or career highlights

   Products or Services

   Overview of what the company offers

   Detailed breakdown of key products or services

   Unique value propositions, target customers, or use cases

   Company History / Timeline

   Founding story

   Key milestones, pivots, or growth events

   Funding rounds or investor info (if available)

   Customer Base or Markets

   Who the company serves

   Industries or regions it operates in

   Testimonials or case studies (if available)

   Culture & Values

   Company culture and principles

   Any community involvement or sustainability efforts

   Press, Recognition, or Partnerships

   Awards, recognitions, or notable press mentions

   Strategic partners or integrations

   Contact and Socials

   Extract general contact info if available (email, phone)

   List of social media handles (LinkedIn, Twitter, Instagram, etc.)

   ⚠️ What Not to Include:
   Do not scrape HTML/CSS/JS or source code.

   Do not include boilerplate UI content (like “Welcome to our site!” headers).

   Do not include legal pages (Privacy Policy, Terms & Conditions).

Output Format:
The final output should be a single, well-written article, similar to a professional company profile in a business magazine or investor briefing. Use clear headings (like Founders, Products, Company History, etc.) and natural transitions. Avoid bullet lists unless summarizing something."""
      
    return prompt