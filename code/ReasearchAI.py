#!/usr/bin/env python3
"""
Autonomous Legal Research System - Enhanced Version
A comprehensive AI-powered legal research tool with intelligent content extraction
"""

import os
import json
import time
import asyncio
import threading
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Core libraries
import requests
from bs4 import BeautifulSoup
import wikipedia
import PyPDF2
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# GUI imports - marker: GUI_START
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
# GUI imports - marker: GUI_END

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegalResearchConfig:
    """Configuration class for the legal research system"""
    
    def __init__(self):
        # API Configuration
        self.GEMINI_API_KEY = "AIzaSyD_l-YT3SqAgnMf-6pzA_3oAuCtuCjR-K4"  # Update this with your actual API key
        self.GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
        # Search parameters
        self.MAX_SEARCH_RESULTS = 15
        self.MAX_WIKIPEDIA_PAGES = 8
        self.MIN_CONTENT_LENGTH = 200
        self.MAX_CONTENT_LENGTH = 5000
        
        # Legal domains for multi-agent setup
        self.LEGAL_DOMAINS = {
            'contracts': 'Contract Law, Agreement Analysis, Terms and Conditions, Breach of Contract',
            'criminal': 'Criminal Law, Prosecution, Defense, Evidence, Criminal Procedure',
            'ip': 'Intellectual Property, Patents, Trademarks, Copyright, Trade Secrets',
            'corporate': 'Corporate Law, Business Regulations, Compliance, Securities',
            'family': 'Family Law, Divorce, Custody, Marriage, Domestic Relations',
            'employment': 'Employment Law, Labor Rights, Workplace Issues, Discrimination',
            'real_estate': 'Property Law, Real Estate Transactions, Zoning, Land Use',
            'tax': 'Tax Law, Revenue, Deductions, Compliance, Tax Planning'
        }
        
        # Legal content indicators
        self.LEGAL_KEYWORDS = [
            'case law', 'precedent', 'statute', 'regulation', 'court', 'judge', 'ruling',
            'verdict', 'legal', 'law', 'attorney', 'lawyer', 'jurisdiction', 'appeal',
            'litigation', 'contract', 'agreement', 'liability', 'damages', 'plaintiff',
            'defendant', 'evidence', 'testimony', 'witness', 'legal principle'
        ]

class EnhancedWebSearchAgent:
    """Enhanced agent with better content extraction and processing"""
    
    def __init__(self, config: LegalResearchConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def enhanced_google_search(self, query: str, num_results: int = 15) -> List[Dict[str, str]]:
        """Enhanced Google search with better content extraction"""
        try:
            # Multiple search engines for better coverage
            results = []
            
            # DuckDuckGo search
            duckduck_results = self._search_duckduckgo(query, num_results//2)
            results.extend(duckduck_results)
            
            # Add legal-specific search terms
            legal_query = f"{query} law legal case court ruling statute"
            legal_results = self._search_duckduckgo(legal_query, num_results//2)
            results.extend(legal_results)
            
            # Remove duplicates and filter by relevance
            unique_results = self._deduplicate_results(results)
            relevant_results = self._filter_legal_relevance(unique_results)
            
            # Extract detailed content from top results
            enhanced_results = self._extract_detailed_content(relevant_results[:10])
            
            logger.info(f"Enhanced search found {len(enhanced_results)} relevant legal sources")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in enhanced search: {str(e)}")
            return []

    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Search DuckDuckGo with better parsing"""
        try:
            search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
            response = self.session.get(search_url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            result_divs = soup.find_all('div', class_='result')[:num_results]
            
            for div in result_divs:
                title_elem = div.find('a', class_='result__a')
                snippet_elem = div.find('a', class_='result__snippet')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # Clean and enhance snippet
                    if snippet:
                        snippet = self._clean_text(snippet)
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'duckduckgo'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {str(e)}")
            return []

    def _extract_detailed_content(self, results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Extract detailed content from search result URLs"""
        enhanced_results = []
        
        for result in results:
            try:
                if not result.get('url'):
                    continue
                    
                # Skip non-web URLs
                if not result['url'].startswith(('http://', 'https://')):
                    continue
                
                response = self.session.get(result['url'], timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
                    element.decompose()
                
                # Extract main content
                content = self._extract_main_content(soup)
                
                if len(content) >= self.config.MIN_CONTENT_LENGTH:
                    result['detailed_content'] = content[:self.config.MAX_CONTENT_LENGTH]
                    result['content_length'] = len(content)
                    result['legal_score'] = self._calculate_legal_relevance_score(content)
                    enhanced_results.append(result)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Failed to extract content from {result.get('url', 'unknown')}: {str(e)}")
                # Keep original result even if content extraction fails
                result['detailed_content'] = result.get('snippet', '')
                result['legal_score'] = self._calculate_legal_relevance_score(result.get('snippet', ''))
                enhanced_results.append(result)
                continue
        
        # Sort by legal relevance score
        enhanced_results.sort(key=lambda x: x.get('legal_score', 0), reverse=True)
        return enhanced_results

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from webpage"""
        # Try common content containers
        content_selectors = [
            'main', 'article', '.content', '#content', '.main-content',
            '.post-content', '.entry-content', '.page-content', 'section'
        ]
        
        content_text = ""
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    text = element.get_text(separator=' ', strip=True)
                    if len(text) > len(content_text):
                        content_text = text
                break
        
        # Fallback to body content
        if not content_text or len(content_text) < self.config.MIN_CONTENT_LENGTH:
            body = soup.find('body')
            if body:
                content_text = body.get_text(separator=' ', strip=True)
        
        return self._clean_and_structure_text(content_text)

    def _clean_and_structure_text(self, text: str) -> str:
        """Clean and structure extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common website elements
        unwanted_patterns = [
            r'cookie policy.*?accept',
            r'subscribe.*?newsletter',
            r'follow us.*?social',
            r'advertisement',
            r'sponsored content',
            r'related articles',
            r'share this.*?twitter'
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Extract paragraphs and legal sections
        sentences = text.split('.')
        relevant_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and self._is_legal_relevant(sentence):
                relevant_sentences.append(sentence)
        
        return '. '.join(relevant_sentences)

    def _is_legal_relevant(self, text: str) -> bool:
        """Check if text contains legal content"""
        text_lower = text.lower()
        legal_terms_found = sum(1 for keyword in self.config.LEGAL_KEYWORDS if keyword in text_lower)
        return legal_terms_found >= 1

    def _calculate_legal_relevance_score(self, text: str) -> float:
        """Calculate relevance score for legal content"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        # Count legal keywords
        for keyword in self.config.LEGAL_KEYWORDS:
            score += text_lower.count(keyword) * 2
        
        # Bonus for legal phrases
        legal_phrases = [
            'case law', 'legal precedent', 'court ruling', 'statute provides',
            'legal principle', 'court held', 'legal standard', 'applicable law'
        ]
        
        for phrase in legal_phrases:
            score += text_lower.count(phrase) * 3
        
        # Normalize by text length
        return min(score / (len(text) / 100), 10.0)

    def _deduplicate_results(self, results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicate results"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results

    def _filter_legal_relevance(self, results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Filter results by legal relevance"""
        relevant_results = []
        
        for result in results:
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            combined_text = f"{title} {snippet}"
            
            # Check for legal relevance
            if self._is_legal_relevant(combined_text):
                relevant_results.append(result)
        
        return relevant_results

    def enhanced_wikipedia_search(self, topic: str, max_pages: int = 8) -> List[Dict[str, str]]:
        """Enhanced Wikipedia search with better content extraction"""
        try:
            # Multiple search strategies
            search_queries = [
                topic,
                f"{topic} law",
                f"{topic} legal",
                f"{topic} case law",
                f"{topic} legislation"
            ]
            
            all_pages = []
            seen_titles = set()
            
            for query in search_queries:
                try:
                    search_results = wikipedia.search(query, results=max_pages//len(search_queries))
                    
                    for title in search_results:
                        if title.lower() in seen_titles:
                            continue
                        seen_titles.add(title.lower())
                        
                        try:
                            page = wikipedia.page(title)
                            
                            # Extract structured content
                            content_sections = self._extract_wikipedia_sections(page)
                            legal_score = self._calculate_legal_relevance_score(page.content)
                            
                            if legal_score > 1.0:  # Only include legally relevant pages
                                all_pages.append({
                                    'title': page.title,
                                    'url': page.url,
                                    'summary': page.summary,
                                    'content_sections': content_sections,
                                    'full_content': page.content[:3000],
                                    'legal_score': legal_score,
                                    'source': 'wikipedia'
                                })
                                
                        except wikipedia.exceptions.DisambiguationError as e:
                            # Try first disambiguation option
                            try:
                                page = wikipedia.page(e.options[0])
                                content_sections = self._extract_wikipedia_sections(page)
                                legal_score = self._calculate_legal_relevance_score(page.content)
                                
                                if legal_score > 1.0:
                                    all_pages.append({
                                        'title': page.title,
                                        'url': page.url,
                                        'summary': page.summary,
                                        'content_sections': content_sections,
                                        'full_content': page.content[:3000],
                                        'legal_score': legal_score,
                                        'source': 'wikipedia'
                                    })
                            except:
                                continue
                        except:
                            continue
                            
                except Exception as e:
                    logger.warning(f"Wikipedia search error for '{query}': {str(e)}")
                    continue
            
            # Sort by legal relevance and limit results
            all_pages.sort(key=lambda x: x['legal_score'], reverse=True)
            logger.info(f"Enhanced Wikipedia search found {len(all_pages)} relevant legal articles")
            return all_pages[:max_pages]
            
        except Exception as e:
            logger.error(f"Error in enhanced Wikipedia search: {str(e)}")
            return []

    def _extract_wikipedia_sections(self, page) -> Dict[str, str]:
        """Extract relevant sections from Wikipedia page"""
        sections = {}
        content = page.content
        
        # Split by section headers (== Section ==)
        section_pattern = r'\n\n==\s*([^=]+)\s*==\n'
        parts = re.split(section_pattern, content)
        
        current_section = "Introduction"
        sections[current_section] = parts[0] if parts else ""
        
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                section_title = parts[i].strip()
                section_content = parts[i + 1].strip()
                
                # Only include sections with legal relevance
                if self._is_legal_relevant(f"{section_title} {section_content}"):
                    sections[section_title] = section_content[:1000]  # Limit section length
        
        return sections

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]]', '', text)
        
        return text

class EnhancedGeminiAnalysisAgent:
    """Enhanced AI analysis agent with better prompting and processing"""
    
    def __init__(self, config: LegalResearchConfig):
        self.config = config
        self.api_url = f"{config.GEMINI_API_URL}?key={config.GEMINI_API_KEY}"

    def analyze_legal_data(self, topic: str, search_data: List[Dict], wiki_data: List[Dict], domain: str = 'general') -> Dict[str, Any]:
        """Enhanced analysis with better prompting and content processing"""
        try:
            # Prepare comprehensive data summary
            processed_search_data = self._process_search_data(search_data)
            processed_wiki_data = self._process_wiki_data(wiki_data)
            
            domain_context = self.config.LEGAL_DOMAINS.get(domain, 'General Legal Research')
            
            # Create a more structured and detailed prompt
            prompt = self._create_enhanced_prompt(topic, processed_search_data, processed_wiki_data, domain_context)
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "topK": 40,
                    "topP": 0.8,
                    "maxOutputTokens": 8192
                }
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result['candidates'][0]['content']['parts'][0]['text']
                
                # Post-process analysis for better formatting
                formatted_analysis = self._format_analysis_output(analysis)
                
                return {
                    'topic': topic,
                    'domain': domain,
                    'analysis': formatted_analysis,
                    'timestamp': datetime.now().isoformat(),
                    'sources_count': len(search_data) + len(wiki_data),
                    'data_quality_score': self._calculate_data_quality(search_data, wiki_data)
                }
            else:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return self._create_enhanced_fallback_analysis(topic, search_data, wiki_data, domain)
                
        except Exception as e:
            logger.error(f"Error in enhanced Gemini analysis: {str(e)}")
            return self._create_enhanced_fallback_analysis(topic, search_data, wiki_data, domain)

    def _process_search_data(self, search_data: List[Dict]) -> Dict[str, Any]:
        """Process and summarize search data"""
        if not search_data:
            return {'summary': 'No search data available', 'key_points': [], 'sources': []}
        
        key_points = []
        sources = []
        total_content_length = 0
        
        for item in search_data:
            content = item.get('detailed_content', item.get('snippet', ''))
            if content and len(content) > 50:
                # Extract key sentences
                sentences = content.split('.')
                for sentence in sentences[:3]:  # Take first 3 sentences
                    sentence = sentence.strip()
                    if len(sentence) > 20 and self._is_meaningful_sentence(sentence):
                        key_points.append(sentence)
                
                sources.append({
                    'title': item.get('title', 'Unknown'),
                    'url': item.get('url', ''),
                    'relevance_score': item.get('legal_score', 0),
                    'content_preview': content[:200] + '...' if len(content) > 200 else content
                })
                
                total_content_length += len(content)
        
        return {
            'summary': f"Processed {len(search_data)} web sources with {total_content_length} characters of content",
            'key_points': key_points[:15],  # Limit key points
            'sources': sources,
            'total_sources': len(search_data)
        }

    def _process_wiki_data(self, wiki_data: List[Dict]) -> Dict[str, Any]:
        """Process and summarize Wikipedia data"""
        if not wiki_data:
            return {'summary': 'No Wikipedia data available', 'articles': [], 'key_sections': {}}
        
        articles = []
        key_sections = {}
        
        for item in wiki_data:
            articles.append({
                'title': item.get('title', 'Unknown'),
                'url': item.get('url', ''),
                'summary': item.get('summary', '')[:300],
                'relevance_score': item.get('legal_score', 0)
            })
            
            # Extract key sections
            sections = item.get('content_sections', {})
            for section_name, section_content in sections.items():
                if len(section_content) > 100:
                    key_sections[f"{item.get('title', 'Unknown')} - {section_name}"] = section_content[:500]
        
        return {
            'summary': f"Processed {len(wiki_data)} Wikipedia articles",
            'articles': articles,
            'key_sections': key_sections,
            'total_articles': len(wiki_data)
        }

    def _create_enhanced_prompt(self, topic: str, search_data: Dict, wiki_data: Dict, domain_context: str) -> str:
        """Create a comprehensive and structured prompt for AI analysis"""
        return f"""
        You are an expert legal researcher and analyst specializing in {domain_context}. 
        
        RESEARCH TASK: Conduct a comprehensive legal analysis on "{topic}"
        
        AVAILABLE DATA:
        
        1. WEB SEARCH FINDINGS:
        {search_data['summary']}
        
        Key Legal Points Found:
        {chr(10).join(f"• {point}" for point in search_data['key_points'][:10])}
        
        Primary Sources:
        {chr(10).join(f"- {source['title']}: {source['content_preview']}" for source in search_data['sources'][:5])}
        
        2. WIKIPEDIA RESEARCH:
        {wiki_data['summary']}
        
        Relevant Articles:
        {chr(10).join(f"• {article['title']}: {article['summary']}" for article in wiki_data['articles'][:5])}
        
        Key Legal Sections:
        {chr(10).join(f"- {section}: {content[:200]}..." for section, content in list(wiki_data['key_sections'].items())[:3])}
        
        ANALYSIS REQUIREMENTS:
        Please provide a detailed legal research report with the following structure:
        
        ## EXECUTIVE SUMMARY
        Provide a clear, concise overview of the legal topic and key findings (2-3 paragraphs)
        
        ## LEGAL FRAMEWORK AND PRINCIPLES
        Detail the fundamental legal principles, statutes, and regulations governing this area
        
        ## CASE LAW AND PRECEDENTS  
        Identify and analyze key court decisions, legal precedents, and their implications
        
        ## CURRENT LEGAL STATUS
        Explain the current state of the law, recent developments, and jurisdictional variations
        
        ## PRACTICAL IMPLICATIONS
        Discuss real-world applications, compliance requirements, and practical considerations
        
        ## RISK ANALYSIS
        Identify potential legal risks, liabilities, and areas of uncertainty
        
        ## STRATEGIC RECOMMENDATIONS
        Provide actionable legal guidance and best practices
        
        ## AREAS FOR FURTHER RESEARCH
        Suggest specific areas requiring additional investigation or expert consultation
        
        IMPORTANT GUIDELINES:
        - Base your analysis on the provided research data
        - Cite specific sources and examples from the data
        - Provide practical, actionable insights
        - Highlight any limitations or gaps in the available information
        - Use professional legal terminology while remaining accessible
        - Include specific legal citations and references where available in the source material
        
        Please ensure your analysis is comprehensive, well-structured, and professionally written.
        """

    def _format_analysis_output(self, analysis: str) -> str:
        """Format the AI analysis output for better readability"""
        # Clean up the analysis text
        analysis = re.sub(r'\*\*(.*?)\*\*', r'\1', analysis)  # Remove markdown bold
        analysis = re.sub(r'\*(.*?)\*', r'\1', analysis)      # Remove markdown italic
        analysis = re.sub(r'\n\s*\n\s*\n', '\n\n', analysis)  # Remove excessive line breaks
        
        # Ensure proper section formatting
        section_headers = [
            'EXECUTIVE SUMMARY', 'LEGAL FRAMEWORK AND PRINCIPLES', 'CASE LAW AND PRECEDENTS',
            'CURRENT LEGAL STATUS', 'PRACTICAL IMPLICATIONS', 'RISK ANALYSIS',
            'STRATEGIC RECOMMENDATIONS', 'AREAS FOR FURTHER RESEARCH'
        ]
        
        for header in section_headers:
            pattern = rf'#+\s*{header}|{header}:?'
            replacement = f'\n{header}\n{"="*len(header)}'
            analysis = re.sub(pattern, replacement, analysis, flags=re.IGNORECASE)
        
        return analysis.strip()

    def _create_enhanced_fallback_analysis(self, topic: str, search_data: List[Dict], wiki_data: List[Dict], domain: str) -> Dict[str, Any]:
        """Create an enhanced fallback analysis when AI API is unavailable"""
        
        domain_context = self.config.LEGAL_DOMAINS.get(domain, 'General Legal Research')
        
        analysis = f"""
LEGAL RESEARCH REPORT: {topic.upper()}
========================================

DOMAIN: {domain_context}
RESEARCH DATE: {datetime.now().strftime('%B %d, %Y')}
SOURCES ANALYZED: {len(search_data)} web sources, {len(wiki_data)} Wikipedia articles

EXECUTIVE SUMMARY
=================
This comprehensive legal research report examines {topic} within the context of {domain_context.lower()}. 
The analysis is based on {len(search_data) + len(wiki_data)} sources including legal websites, 
academic articles, and authoritative Wikipedia entries.

RESEARCH FINDINGS
=================
"""
        
        # Add detailed content from search results
        if search_data:
            analysis += "\nWEB SOURCE ANALYSIS:\n"
            for i, result in enumerate(search_data[:5], 1):
                content = result.get('detailed_content', result.get('snippet', ''))
                if content and len(content) > 50:
                    analysis += f"\n{i}. {result.get('title', 'Legal Source')}\n"
                    analysis += f"   URL: {result.get('url', 'N/A')}\n"
                    analysis += f"   Legal Relevance Score: {result.get('legal_score', 0):.1f}/10\n"
                    analysis += f"   Key Content: {content[:400]}...\n"
        
        # Add Wikipedia content
        if wiki_data:
            analysis += "\nWIKIPEDIA RESEARCH:\n"
            for i, wiki in enumerate(wiki_data[:3], 1):
                analysis += f"\n{i}. {wiki.get('title', 'Wikipedia Article')}\n"
                analysis += f"   URL: {wiki.get('url', 'N/A')}\n"
                analysis += f"   Summary: {wiki.get('summary', 'N/A')[:300]}...\n"
                
                # Add section content
                sections = wiki.get('content_sections', {})
                if sections:
                    analysis += "   Key Sections:\n"
                    for section_name, section_content in list(sections.items())[:2]:
                        analysis += f"   - {section_name}: {section_content[:200]}...\n"
        
        analysis += f"""

LEGAL IMPLICATIONS
==================
Based on the research conducted, several key legal considerations emerge regarding {topic}:

1. REGULATORY FRAMEWORK: The legal landscape surrounding {topic} involves multiple 
   jurisdictions and regulatory bodies, each with specific requirements and procedures.

2. COMPLIANCE REQUIREMENTS: Organizations and individuals dealing with {topic} must 
   navigate complex compliance obligations that vary by jurisdiction and context.

3. RISK FACTORS: Key legal risks identified include regulatory non-compliance, 
   contractual disputes, and potential liability issues.

PRACTICAL RECOMMENDATIONS
=========================
1. Consult with qualified legal professionals specializing in {domain_context.lower()}
2. Stay current with regulatory changes and legal developments
3. Implement robust compliance monitoring systems
4. Document all relevant legal procedures and decisions
5. Consider jurisdiction-specific variations in legal requirements

AREAS FOR FURTHER RESEARCH
==========================
1. Recent case law developments and their implications
2. Regulatory updates and proposed legislative changes
3. Jurisdiction-specific legal requirements and procedures
4. Industry-specific compliance standards and best practices
5. Expert legal opinions on emerging issues in {topic}

DATA QUALITY ASSESSMENT
=======================
Sources Evaluated: {len(search_data) + len(wiki_data)}
Content Quality: {"High" if len(search_data) > 5 else "Moderate"}
Legal Relevance: {"Strong" if any(item.get('legal_score', 0) > 5 for item in search_data) else "Moderate"}

IMPORTANT NOTICE
================
This analysis is generated for research purposes only and does not constitute legal advice.
The information provided may not be current or applicable to specific situations.
Always consult with qualified legal professionals for matters requiring legal expertise.

Generated by: Autonomous Legal Research System (Fallback Mode)
Note: For enhanced AI-powered analysis, configure the Gemini API key in the system settings.
"""
        
        return {
            'topic': topic,
            'domain': domain,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat(),
            'sources_count': len(search_data) + len(wiki_data),
            'fallback_mode': True,
            'data_quality_score': self._calculate_data_quality(search_data, wiki_data)
        }

    def _is_meaningful_sentence(self, sentence: str) -> bool:
        """Check if a sentence contains meaningful legal content"""
        sentence_lower = sentence.lower()
        
        # Must contain at least one legal keyword
        has_legal_term = any(keyword in sentence_lower for keyword in self.config.LEGAL_KEYWORDS)
        
        # Must be substantive (not just navigation/UI text)
        meaningless_phrases = ['click here', 'read more', 'subscribe', 'follow us', 'cookie policy']
        has_meaningless = any(phrase in sentence_lower for phrase in meaningless_phrases)
        
        return has_legal_term and not has_meaningless and len(sentence) > 30

    def _calculate_data_quality(self, search_data: List[Dict], wiki_data: List[Dict]) -> float:
        """Calculate overall data quality score"""
        if not search_data and not wiki_data:
            return 0.0
        
        total_score = 0.0
        total_sources = 0
        
        # Evaluate search data quality
        for item in search_data:
            source_score = 0.0
            
            # Content length score (0-3 points)
            content_length = len(item.get('detailed_content', item.get('snippet', '')))
            if content_length > 2000:
                source_score += 3
            elif content_length > 1000:
                source_score += 2
            elif content_length > 500:
                source_score += 1
            
            # Legal relevance score (0-4 points)
            legal_score = item.get('legal_score', 0)
            source_score += min(legal_score / 2.5, 4)
            
            # Source credibility (0-3 points)
            url = item.get('url', '').lower()
            if any(domain in url for domain in ['.gov', '.edu', 'law.', 'legal']):
                source_score += 3
            elif any(domain in url for domain in ['.org', 'court', 'justice']):
                source_score += 2
            elif not any(domain in url for domain in ['blog', 'forum', 'social']):
                source_score += 1
            
            total_score += source_score
            total_sources += 1
        
        # Evaluate Wikipedia data quality
        for item in wiki_data:
            source_score = 5.0  # Wikipedia baseline quality
            
            # Legal relevance bonus
            legal_score = item.get('legal_score', 0)
            source_score += min(legal_score / 2, 3)
            
            # Content completeness bonus
            if item.get('content_sections') and len(item.get('content_sections', {})) > 3:
                source_score += 2
            
            total_score += source_score
            total_sources += 1
        
        # Calculate average and normalize to 0-10 scale
        if total_sources == 0:
            return 0.0
        
        average_score = total_score / total_sources
        return min(average_score, 10.0)


class PDFReportGenerator:
    """Enhanced PDF report generator with professional formatting"""
    
    def __init__(self, config: LegalResearchConfig):
        self.config = config
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for the PDF report"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=20,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceBefore=20,
            spaceAfter=12,
            borderWidth=1,
            borderColor=colors.darkblue,
            borderPadding=5
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.darkslategray,
            spaceBefore=15,
            spaceAfter=8
        ))
        
        # Body text with better spacing
        self.styles.add(ParagraphStyle(
            name='BodyTextSpaced',
            parent=self.styles['BodyText'],
            spaceBefore=6,
            spaceAfter=6,
            alignment=0  # Left alignment
        ))
        
        # Source citation style
        self.styles.add(ParagraphStyle(
            name='SourceCitation',
            parent=self.styles['BodyText'],
            fontSize=9,
            textColor=colors.darkgray,
            leftIndent=20,
            spaceBefore=3,
            spaceAfter=3
        ))

    def generate_report(self, analysis_result: Dict[str, Any], filename: str = None) -> str:
        """Generate a comprehensive PDF report from analysis results"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                topic_clean = re.sub(r'[^\w\s-]', '', analysis_result.get('topic', 'legal_research'))
                topic_clean = re.sub(r'[-\s]+', '_', topic_clean)
                filename = f"legal_research_{topic_clean}_{timestamp}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build document content
            story = []
            
            # Title page
            self._add_title_page(story, analysis_result)
            
            # Table of contents
            self._add_table_of_contents(story)
            
            # Executive summary
            self._add_executive_summary(story, analysis_result)
            
            # Main analysis content
            self._add_analysis_content(story, analysis_result)
            
            # Source appendix
            self._add_source_appendix(story, analysis_result)
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report generated successfully: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return None

    def _add_title_page(self, story: List, analysis_result: Dict[str, Any]):
        """Add title page to the report"""
        # Main title
        title = f"Legal Research Report: {analysis_result.get('topic', 'Unknown Topic')}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Subtitle
        domain = analysis_result.get('domain', 'general')
        domain_context = self.config.LEGAL_DOMAINS.get(domain, 'General Legal Research')
        subtitle = f"Domain: {domain_context}"
        story.append(Paragraph(subtitle, self.styles['Heading2']))
        story.append(Spacer(1, 30))
        
        # Report metadata table
        metadata = [
            ['Report Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
            ['Research Topic:', analysis_result.get('topic', 'N/A')],
            ['Legal Domain:', domain_context],
            ['Sources Analyzed:', str(analysis_result.get('sources_count', 0))],
            ['Data Quality Score:', f"{analysis_result.get('data_quality_score', 0):.1f}/10"],
            ['Analysis Mode:', 'AI-Enhanced' if not analysis_result.get('fallback_mode') else 'Fallback Mode']
        ]
        
        metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 40))
        
        # Disclaimer
        disclaimer_text = """
        IMPORTANT LEGAL DISCLAIMER: This report is generated for research and informational 
        purposes only and does not constitute legal advice. The information contained herein 
        may not be current, complete, or applicable to specific legal situations. Always 
        consult with qualified legal professionals for matters requiring legal expertise 
        and before making any legal decisions.
        """
        story.append(Paragraph(disclaimer_text, self.styles['BodyText']))
        story.append(Spacer(1, 12))
        
        # Page break
        story.append(Spacer(1, 200))

    def _add_table_of_contents(self, story: List):
        """Add table of contents"""
        story.append(Paragraph("TABLE OF CONTENTS", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        toc_items = [
            "1. Executive Summary",
            "2. Legal Framework and Principles", 
            "3. Case Law and Precedents",
            "4. Current Legal Status",
            "5. Practical Implications",
            "6. Risk Analysis",
            "7. Strategic Recommendations",
            "8. Areas for Further Research",
            "9. Source References"
        ]
        
        for item in toc_items:
            story.append(Paragraph(item, self.styles['BodyText']))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 30))

    def _add_executive_summary(self, story: List, analysis_result: Dict[str, Any]):
        """Add executive summary section"""
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        analysis_text = analysis_result.get('analysis', '')
        
        # Extract executive summary from analysis
        exec_summary = self._extract_section(analysis_text, 'EXECUTIVE SUMMARY')
        if exec_summary:
            paragraphs = exec_summary.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), self.styles['BodyTextSpaced']))
                    story.append(Spacer(1, 6))
        else:
            # Default executive summary
            default_summary = f"""
            This comprehensive legal research report examines {analysis_result.get('topic', 'the specified topic')} 
            and provides detailed analysis based on {analysis_result.get('sources_count', 0)} sources. 
            The research covers fundamental legal principles, current regulations, case law precedents, 
            and practical implications for legal practitioners and stakeholders.
            """
            story.append(Paragraph(default_summary.strip(), self.styles['BodyTextSpaced']))
        
        story.append(Spacer(1, 20))

    def _add_analysis_content(self, story: List, analysis_result: Dict[str, Any]):
        """Add main analysis content sections"""
        analysis_text = analysis_result.get('analysis', '')
        
        sections = [
            'LEGAL FRAMEWORK AND PRINCIPLES',
            'CASE LAW AND PRECEDENTS', 
            'CURRENT LEGAL STATUS',
            'PRACTICAL IMPLICATIONS',
            'RISK ANALYSIS',
            'STRATEGIC RECOMMENDATIONS',
            'AREAS FOR FURTHER RESEARCH'
        ]
        
        for section_title in sections:
            section_content = self._extract_section(analysis_text, section_title)
            if section_content:
                story.append(Paragraph(section_title, self.styles['SectionHeader']))
                story.append(Spacer(1, 12))
                
                paragraphs = section_content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        # Check if it's a sub-header (numbered items, bullet points, etc.)
                        if re.match(r'^\d+\.', para.strip()) or para.strip().startswith('•'):
                            story.append(Paragraph(para.strip(), self.styles['SubsectionHeader']))
                        else:
                            story.append(Paragraph(para.strip(), self.styles['BodyTextSpaced']))
                        story.append(Spacer(1, 6))
                
                story.append(Spacer(1, 15))

    def _add_source_appendix(self, story: List, analysis_result: Dict[str, Any]):
        """Add source references appendix"""
        story.append(Paragraph("SOURCE REFERENCES", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Extract source information if available in analysis
        analysis_text = analysis_result.get('analysis', '')
        
        # Look for source sections in the analysis
        sources_section = self._extract_section(analysis_text, 'WEB SOURCE ANALYSIS')
        if sources_section:
            story.append(Paragraph("Web Sources:", self.styles['SubsectionHeader']))
            story.append(Spacer(1, 8))
            
            # Parse and format web sources
            source_entries = re.split(r'\n\d+\.', sources_section)
            for entry in source_entries[1:]:  # Skip first empty split
                if entry.strip():
                    story.append(Paragraph(f"• {entry.strip()}", self.styles['SourceCitation']))
                    story.append(Spacer(1, 4))
        
        wiki_section = self._extract_section(analysis_text, 'WIKIPEDIA RESEARCH')
        if wiki_section:
            story.append(Spacer(1, 12))
            story.append(Paragraph("Wikipedia Sources:", self.styles['SubsectionHeader']))
            story.append(Spacer(1, 8))
            
            # Parse and format Wikipedia sources
            wiki_entries = re.split(r'\n\d+\.', wiki_section)
            for entry in wiki_entries[1:]:  # Skip first empty split
                if entry.strip():
                    story.append(Paragraph(f"• {entry.strip()}", self.styles['SourceCitation']))
                    story.append(Spacer(1, 4))
        
        # Add generation info
        story.append(Spacer(1, 20))
        generation_info = f"""
        Report generated by Autonomous Legal Research System v2.0
        Generation timestamp: {analysis_result.get('timestamp', 'Unknown')}
        Data quality score: {analysis_result.get('data_quality_score', 0):.1f}/10
        Total sources analyzed: {analysis_result.get('sources_count', 0)}
        """
        story.append(Paragraph(generation_info.strip(), self.styles['SourceCitation']))

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from the analysis text"""
        # Try to find section with equals underline
        pattern = rf'{section_name}\n=+\n(.*?)(?=\n[A-Z][A-Z\s]+\n=+|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Try alternative format
        pattern = rf'{section_name}:?\n(.*?)(?=\n[A-Z][A-Z\s]+:?|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return ""


class LegalResearchGUI:
    """Enhanced GUI for the legal research system"""
    
    def __init__(self):
        self.config = LegalResearchConfig()
        self.search_agent = EnhancedWebSearchAgent(self.config)
        self.ai_agent = EnhancedGeminiAnalysisAgent(self.config)
        self.pdf_generator = PDFReportGenerator(self.config)
        
        self.root = tk.Tk()
        self.root.title("Autonomous Legal Research System v2.0")
        self.root.geometry("1200x800")
        
        # Research results storage
        self.current_results = None
        
        self._setup_gui()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup GUI styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Research.TButton', font=('Helvetica', 10, 'bold'))
    
    def _setup_gui(self):
        """Setup the main GUI interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Autonomous Legal Research System", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Research topic input
        ttk.Label(main_frame, text="Research Topic:", style='Header.TLabel').grid(
            row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        self.topic_var = tk.StringVar()
        topic_entry = ttk.Entry(main_frame, textvariable=self.topic_var, width=50)
        topic_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Legal domain selection
        ttk.Label(main_frame, text="Legal Domain:", style='Header.TLabel').grid(
            row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        self.domain_var = tk.StringVar(value='general')
        domain_dropdown = ttk.Combobox(main_frame, textvariable=self.domain_var, 
                                     values=list(self.config.LEGAL_DOMAINS.keys()))
        domain_dropdown.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        # Research button
        self.research_button = ttk.Button(button_frame, text="Start Research", 
                                        command=self._start_research,
                                        style='Research.TButton')
        self.research_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Export PDF button
        self.pdf_button = ttk.Button(button_frame, text="Export PDF", 
                                   command=self._export_pdf, state='disabled')
        self.pdf_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Settings button
        settings_button = ttk.Button(button_frame, text="Settings", 
                                   command=self._open_settings)
        settings_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                          maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), 
                              pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to start research")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=5, column=0, columnspan=3, sticky=tk.W)
        
        # Results display area with tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), 
                          pady=(10, 0))
        
        # Analysis tab
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="Analysis Report")
        
        self.analysis_text = scrolledtext.ScrolledText(self.analysis_frame, 
                                                     wrap=tk.WORD, width=80, height=25)
        self.analysis_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sources tab
        self.sources_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sources_frame, text="Source Data")
        
        self.sources_text = scrolledtext.ScrolledText(self.sources_frame, 
                                                    wrap=tk.WORD, width=80, height=25)
        self.sources_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bind enter key to start research
        topic_entry.bind('<Return>', lambda e: self._start_research())
    
    def _start_research(self):
        """Start the research process in a separate thread"""
        topic = self.topic_var.get().strip()
        if not topic:
            messagebox.showerror("Error", "Please enter a research topic")
            return
        
        # Disable research button during processing
        self.research_button.config(state='disabled')
        self.pdf_button.config(state='disabled')
        
        # Clear previous results
        self.analysis_text.delete(1.0, tk.END)
        self.sources_text.delete(1.0, tk.END)
        
        # Start research in separate thread
        research_thread = threading.Thread(target=self._conduct_research, 
                                         args=(topic, self.domain_var.get()))
        research_thread.daemon = True
        research_thread.start()
    
    def _conduct_research(self, topic: str, domain: str):
        """Conduct the actual research process"""
        try:
            # Update progress and status
            self._update_progress(10, "Starting web search...")
            
            # Web search
            search_results = self.search_agent.enhanced_google_search(topic)
            self._update_progress(40, f"Found {len(search_results)} web sources")
            
            # Wikipedia search
            self._update_progress(50, "Searching Wikipedia...")
            wiki_results = self.search_agent.enhanced_wikipedia_search(topic)
            self._update_progress(70, f"Found {len(wiki_results)} Wikipedia articles")
            
            # AI Analysis
            self._update_progress(80, "Analyzing data with AI...")
            analysis_results = self.ai_agent.analyze_legal_data(topic, search_results, 
                                                              wiki_results, domain)
            
            # Store results
            self.current_results = {
                'analysis': analysis_results,
                'search_data': search_results,
                'wiki_data': wiki_results
            }
            
            # Update GUI with results
            self._update_progress(100, "Research completed successfully")
            self._display_results()
            
        except Exception as e:
            logger.error(f"Research error: {str(e)}")
            self._update_status(f"Research failed: {str(e)}")
        finally:
            # Re-enable buttons
            self.root.after(0, lambda: self.research_button.config(state='normal'))
            if self.current_results:
                self.root.after(0, lambda: self.pdf_button.config(state='normal'))
    
    def _display_results(self):
        """Display research results in the GUI"""
        if not self.current_results:
            return
        
        # Display analysis
        analysis = self.current_results['analysis'].get('analysis', '')
        self.root.after(0, lambda: self._update_analysis_display(analysis))
        
        # Display source data
        source_summary = self._format_source_summary()
        self.root.after(0, lambda: self._update_sources_display(source_summary))
    
    def _update_analysis_display(self, analysis: str):
        """Update the analysis display"""
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(1.0, analysis)
    
    def _update_sources_display(self, source_summary: str):
        """Update the sources display"""
        self.sources_text.delete(1.0, tk.END)
        self.sources_text.insert(1.0, source_summary)
    
    def _format_source_summary(self) -> str:
        """Format source data for display"""
        if not self.current_results:
            return ""
        
        summary = "RESEARCH SOURCES SUMMARY\n"
        summary += "=" * 50 + "\n\n"
        
        # Web sources
        search_data = self.current_results.get('search_data', [])
        if search_data:
            summary += f"WEB SOURCES ({len(search_data)} found):\n"
            summary += "-" * 30 + "\n"
            
            for i, source in enumerate(search_data[:10], 1):
                summary += f"{i}. {source.get('title', 'Unknown Title')}\n"
                summary += f"   URL: {source.get('url', 'N/A')}\n"
                summary += f"   Legal Score: {source.get('legal_score', 0):.1f}/10\n"
                content = source.get('detailed_content', source.get('snippet', ''))
                if content:
                    summary += f"   Preview: {content[:200]}...\n"
                summary += "\n"
        
        # Wikipedia sources
        wiki_data = self.current_results.get('wiki_data', [])
        if wiki_data:
            summary += f"\nWIKIPEDIA SOURCES ({len(wiki_data)} found):\n"
            summary += "-" * 35 + "\n"
            
            for i, source in enumerate(wiki_data, 1):
                summary += f"{i}. {source.get('title', 'Unknown Title')}\n"
                summary += f"   URL: {source.get('url', 'N/A')}\n"
                summary += f"   Legal Score: {source.get('legal_score', 0):.1f}/10\n"
                summary += f"   Summary: {source.get('summary', 'N/A')[:200]}...\n"
                summary += "\n"
        
        return summary
    
    def _export_pdf(self):
        """Export current results to PDF"""
        if not self.current_results:
            messagebox.showerror("Error", "No research results to export")
            return
        
        try:
            # Ask user for filename
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save Legal Research Report"
            )
            
            if filename:
                self._update_status("Generating PDF report...")
                
                # Generate PDF in separate thread
                pdf_thread = threading.Thread(target=self._generate_pdf_report, 
                                            args=(filename,))
                pdf_thread.daemon = True
                pdf_thread.start()
        
        except Exception as e:
            logger.error(f"PDF export error: {str(e)}")
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")
    
    def _generate_pdf_report(self, filename: str):
        """Generate PDF report in background thread"""
        try:
            result_filename = self.pdf_generator.generate_report(
                self.current_results['analysis'], filename)
            
            if result_filename:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", f"PDF report saved successfully:\n{result_filename}"))
                self._update_status("PDF export completed")
            else:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", "Failed to generate PDF report"))
                self._update_status("PDF export failed")
        
        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", f"PDF generation failed: {str(e)}"))
    
    def _open_settings(self):
        """Open settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # API Key setting
        ttk.Label(settings_window, text="Gemini API Key:", 
                 font=('Helvetica', 10, 'bold')).pack(pady=(20, 5))
        
        api_key_var = tk.StringVar(value=self.config.GEMINI_API_KEY)
        api_key_entry = ttk.Entry(settings_window, textvariable=api_key_var, 
                                 width=60, show="*")
        api_key_entry.pack(pady=(0, 10))
        
        # Search parameters
        ttk.Label(settings_window, text="Search Parameters:", 
                 font=('Helvetica', 10, 'bold')).pack(pady=(20, 10))
        
        params_frame = ttk.Frame(settings_window)
        params_frame.pack(pady=(0, 20))
        
        # Max search results
        ttk.Label(params_frame, text="Max Search Results:").grid(row=0, column=0, 
                                                                sticky=tk.W, padx=(0, 10))
        max_results_var = tk.IntVar(value=self.config.MAX_SEARCH_RESULTS)
        ttk.Spinbox(params_frame, from_=5, to=50, textvariable=max_results_var, 
                   width=10).grid(row=0, column=1, sticky=tk.W)
        
        # Max Wikipedia pages
       
        ttk.Label(params_frame, text="Max Wikipedia Pages:").grid(row=1, column=0,
                                                                  sticky=tk.W, padx=(0, 10), pady=(5, 0))
        max_wiki_var = tk.IntVar(value=self.config.MAX_WIKIPEDIA_PAGES)
        ttk.Spinbox(params_frame, from_=1, to=20, textvariable=max_wiki_var, 
                   width=10).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Content length limits
        ttk.Label(params_frame, text="Min Content Length:").grid(row=2, column=0,
                                                                sticky=tk.W, padx=(0, 10), pady=(5, 0))
        min_content_var = tk.IntVar(value=self.config.MIN_CONTENT_LENGTH)
        ttk.Spinbox(params_frame, from_=100, to=1000, textvariable=min_content_var, 
                   width=10).grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(params_frame, text="Max Content Length:").grid(row=3, column=0,
                                                                sticky=tk.W, padx=(0, 10), pady=(5, 0))
        max_content_var = tk.IntVar(value=self.config.MAX_CONTENT_LENGTH)
        ttk.Spinbox(params_frame, from_=1000, to=10000, textvariable=max_content_var, 
                   width=10).grid(row=3, column=1, sticky=tk.W, pady=(5, 0))
        
        # Buttons frame for settings
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(pady=20)
        
        def save_settings():
            """Save the updated settings"""
            try:
                # Update configuration
                self.config.GEMINI_API_KEY = api_key_var.get().strip()
                self.config.MAX_SEARCH_RESULTS = max_results_var.get()
                self.config.MAX_WIKIPEDIA_PAGES = max_wiki_var.get()
                self.config.MIN_CONTENT_LENGTH = min_content_var.get()
                self.config.MAX_CONTENT_LENGTH = max_content_var.get()
                
                # Update AI agent with new API key
                self.ai_agent = EnhancedGeminiAnalysisAgent(self.config)
                
                messagebox.showinfo("Settings", "Settings saved successfully!")
                settings_window.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
        
        def reset_defaults():
            """Reset to default settings"""
            api_key_var.set("YOUR_GEMINI_API_KEY_HERE")
            max_results_var.set(15)
            max_wiki_var.set(8)
            min_content_var.set(200)
            max_content_var.set(5000)
        
        # Settings buttons
        ttk.Button(button_frame, text="Save Settings", 
                  command=save_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Reset Defaults", 
                  command=reset_defaults).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", 
                  command=settings_window.destroy).pack(side=tk.LEFT)
        
        # Instructions
        instructions = """
Instructions:
1. Enter your Gemini API key to enable AI-powered analysis
2. Adjust search parameters based on your research needs
3. Higher values provide more comprehensive results but take longer
4. Click 'Save Settings' to apply changes
        """
        ttk.Label(settings_window, text=instructions, justify=tk.LEFT, 
                 wraplength=450).pack(pady=20, padx=20)
    
    def _update_progress(self, value: float, status: str):
        """Update progress bar and status"""
        self.root.after(0, lambda: self.progress_var.set(value))
        self.root.after(0, lambda: self.status_var.set(status))
    
    def _update_status(self, status: str):
        """Update status label"""
        self.root.after(0, lambda: self.status_var.set(status))
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


class EnhancedLegalResearchSystem:
    """Main orchestrator class for the enhanced legal research system"""
    
    def __init__(self):
        self.config = LegalResearchConfig()
        self.search_agent = EnhancedWebSearchAgent(self.config)
        self.ai_agent = EnhancedGeminiAnalysisAgent(self.config)
        self.pdf_generator = PDFReportGenerator(self.config)
        
        logger.info("Enhanced Legal Research System initialized")
    
    def conduct_research(self, topic: str, domain: str = 'general', 
                        output_format: str = 'json') -> Dict[str, Any]:
        """
        Conduct comprehensive legal research on a topic
        
        Args:
            topic: Research topic/question
            domain: Legal domain (contracts, criminal, ip, etc.)
            output_format: Output format ('json', 'pdf', 'both')
        
        Returns:
            Dictionary containing research results
        """
        try:
            logger.info(f"Starting research on topic: {topic}")
            logger.info(f"Domain: {domain}")
            
            # Phase 1: Web Search
            logger.info("Phase 1: Conducting web search...")
            search_results = self.search_agent.enhanced_google_search(
                topic, self.config.MAX_SEARCH_RESULTS)
            logger.info(f"Found {len(search_results)} web sources")
            
            # Phase 2: Wikipedia Research
            logger.info("Phase 2: Conducting Wikipedia research...")
            wiki_results = self.search_agent.enhanced_wikipedia_search(
                topic, self.config.MAX_WIKIPEDIA_PAGES)
            logger.info(f"Found {len(wiki_results)} Wikipedia articles")
            
            # Phase 3: AI Analysis
            logger.info("Phase 3: Conducting AI analysis...")
            analysis_results = self.ai_agent.analyze_legal_data(
                topic, search_results, wiki_results, domain)
            logger.info("AI analysis completed")
            
            # Phase 4: Generate outputs
            results = {
                'research_topic': topic,
                'domain': domain,
                'analysis': analysis_results,
                'search_data': search_results,
                'wiki_data': wiki_results,
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_sources': len(search_results) + len(wiki_results),
                    'data_quality_score': analysis_results.get('data_quality_score', 0),
                    'system_version': '2.0'
                }
            }
            
            # Generate PDF if requested
            if output_format in ['pdf', 'both']:
                logger.info("Generating PDF report...")
                pdf_filename = self.pdf_generator.generate_report(analysis_results)
                if pdf_filename:
                    results['pdf_report'] = pdf_filename
                    logger.info(f"PDF report generated: {pdf_filename}")
            
            # Save JSON if requested
            if output_format in ['json', 'both']:
                json_filename = self._save_json_results(results)
                results['json_report'] = json_filename
                logger.info(f"JSON results saved: {json_filename}")
            
            logger.info("Research completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Research failed: {str(e)}")
            raise
    
    def _save_json_results(self, results: Dict[str, Any]) -> str:
        """Save results to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic_clean = re.sub(r'[^\w\s-]', '', results.get('research_topic', 'research'))
            topic_clean = re.sub(r'[-\s]+', '_', topic_clean)
            filename = f"legal_research_{topic_clean}_{timestamp}.json"
            
            # Create a copy without potentially large binary data
            json_results = {
                'research_topic': results.get('research_topic'),
                'domain': results.get('domain'),
                'analysis': results.get('analysis'),
                'metadata': results.get('metadata'),
                'summary': {
                    'total_web_sources': len(results.get('search_data', [])),
                    'total_wiki_sources': len(results.get('wiki_data', [])),
                    'top_web_sources': [
                        {
                            'title': item.get('title'),
                            'url': item.get('url'),
                            'legal_score': item.get('legal_score', 0)
                        }
                        for item in results.get('search_data', [])[:5]
                    ],
                    'top_wiki_sources': [
                        {
                            'title': item.get('title'),
                            'url': item.get('url'),
                            'legal_score': item.get('legal_score', 0)
                        }
                        for item in results.get('wiki_data', [])[:5]
                    ]
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_results, f, indent=2, ensure_ascii=False)
            
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save JSON results: {str(e)}")
            return None


def main():
    """Main function to run the application"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Autonomous Legal Research System v2.0")
    parser.add_argument('--gui', action='store_true', help='Launch GUI interface')
    parser.add_argument('--topic', type=str, help='Research topic for CLI mode')
    parser.add_argument('--domain', type=str, default='general', 
                       help='Legal domain (contracts, criminal, ip, etc.)')
    parser.add_argument('--output', type=str, choices=['json', 'pdf', 'both'], 
                       default='both', help='Output format')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    
    args = parser.parse_args()
    
    try:
        if args.gui or not args.topic:
            # Launch GUI
            logger.info("Launching GUI interface...")
            gui = LegalResearchGUI()
            gui.run()
        else:
            # CLI mode
            logger.info("Running in CLI mode...")
            system = EnhancedLegalResearchSystem()
            
            if args.config:
                # Load custom configuration if provided
                logger.info(f"Loading configuration from: {args.config}")
                # Configuration loading would be implemented here
            
            # Conduct research
            results = system.conduct_research(
                topic=args.topic,
                domain=args.domain,
                output_format=args.output
            )
            
            # Print summary
            print("\n" + "="*60)
            print("LEGAL RESEARCH COMPLETED")
            print("="*60)
            print(f"Topic: {results['research_topic']}")
            print(f"Domain: {results['domain']}")
            print(f"Total Sources: {results['metadata']['total_sources']}")
            print(f"Data Quality: {results['metadata']['data_quality_score']:.1f}/10")
            
            if 'pdf_report' in results:
                print(f"PDF Report: {results['pdf_report']}")
            if 'json_report' in results:
                print(f"JSON Report: {results['json_report']}")
            
            print("\nAnalysis Preview:")
            print("-" * 40)
            analysis_text = results['analysis'].get('analysis', '')
            preview = analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text
            print(preview)
            print("="*60)
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()