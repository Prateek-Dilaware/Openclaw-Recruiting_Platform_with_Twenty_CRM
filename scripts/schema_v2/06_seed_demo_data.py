"""Seed deterministic demo records for every Schema V2 relationship."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from schema_utils import OperationReport, TwentyClient, main_error_boundary


def find_by_name(client: TwentyClient, plural: str, name: str) -> dict[str, Any] | None:
    return next((record for record in client.list_records(plural) if record.get("name") == name), None)


def ensure_record(
    client: TwentyClient,
    report: OperationReport,
    plural: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    existing = find_by_name(client, plural, payload["name"])
    if existing:
        report.skipped.append(f"Demo {plural[:-1]} already exists: {payload['name']}")
        return existing
    try:
        created = client.create_record(plural, payload)
    except httpx.HTTPStatusError as exc:
        response = exc.response
        print(
            "\n[RECORD CREATION FAILED]\n"
            f"Object plural: {plural}\n"
            f"Record name: {payload.get('name')}\n"
            "JSON payload:\n"
            f"{json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True, default=str)}\n"
            f"HTTP status code: {response.status_code}\n"
            "Twenty response body:\n"
            f"{response.text}\n",
            file=sys.stderr,
        )
        raise
    if not created.get("id"):
        raise RuntimeError(f"Twenty did not return an id while creating {plural}: {payload['name']}")
    report.created.append(f"Demo {plural[:-1]}: {payload['name']} ({created['id']})")
    return created


def main() -> None:
    report = OperationReport("Schema V2 demo data seed report")
    client = TwentyClient()
    try:
        required = {"candidate", "requisition", "application", "interview", "evaluation", "offer"}
        missing = required - client.get_object_map().keys()
        if missing:
            raise RuntimeError(f"Schema V2 is incomplete. Missing objects: {', '.join(sorted(missing))}")

        now = datetime.now(timezone.utc).replace(microsecond=0)
        candidate_ada = ensure_record(client, report, "candidates", {
            "name": "Ada Lovelace",
            "emails": {"primaryEmail": "ada.lovelace@example.test", "additionalEmails": []},
            "phones": {"primaryPhoneNumber": "2025550101", "primaryPhoneCountryCode": "US", "primaryPhoneCallingCode": "+1", "additionalPhones": []},
            "source": "Employee Referral", "skillsTags": "Python, FastAPI, PostgreSQL, Docker",
            "resumeUrl": "https://example.test/resumes/ada-lovelace.pdf",
        })
        candidate_grace = ensure_record(client, report, "candidates", {
            "name": "Grace Hopper",
            "emails": {"primaryEmail": "grace.hopper@example.test", "additionalEmails": []},
            "phones": {"primaryPhoneNumber": "2025550102", "primaryPhoneCountryCode": "US", "primaryPhoneCallingCode": "+1", "additionalPhones": []},
            "source": "Career Site", "skillsTags": "React, TypeScript, Testing, Accessibility",
            "resumeUrl": "https://example.test/resumes/grace-hopper.pdf",
        })
        candidate_margaret = ensure_record(client, report, "candidates", {
            "name": "Margaret Hamilton",
            "emails": {"primaryEmail": "margaret.hamilton@example.test", "additionalEmails": []},
            "phones": {"primaryPhoneNumber": "2025550103", "primaryPhoneCountryCode": "US", "primaryPhoneCallingCode": "+1", "additionalPhones": []},
            "source": "Recruiter Sourcing", "skillsTags": "Python, Systems Design, AWS, Leadership",
            "resumeUrl": "https://example.test/resumes/margaret-hamilton.pdf",
        })
        candidate_katherine = ensure_record(client, report, "candidates", {
            "name": "Katherine Johnson",
            "emails": {"primaryEmail": "katherine.johnson@example.test", "additionalEmails": []},
            "phones": {"primaryPhoneNumber": "2025550104", "primaryPhoneCountryCode": "US", "primaryPhoneCallingCode": "+1", "additionalPhones": []},
            "source": "LinkedIn Sourcing", "skillsTags": "Python, Pandas, Machine Learning, Statistics",
            "resumeUrl": "https://example.test/resumes/katherine-johnson.pdf",
        })
        candidate_alan = ensure_record(client, report, "candidates", {
            "name": "Alan Turing",
            "emails": {"primaryEmail": "alan.turing@example.test", "additionalEmails": ["alan.m.turing@example.test"]},
            "phones": {"primaryPhoneNumber": "2079460958", "primaryPhoneCountryCode": "GB", "primaryPhoneCallingCode": "+44", "additionalPhones": []},
            "source": "Referral", "skillsTags": "Kubernetes, Terraform, AWS, CI/CD, Go",
            "resumeUrl": "https://example.test/resumes/alan-turing.pdf",
        })
        candidate_dorothy = ensure_record(client, report, "candidates", {
            "name": "Dorothy Vaughan",
            "emails": {"primaryEmail": "dorothy.vaughan@example.test", "additionalEmails": []},
            "phones": {"primaryPhoneNumber": "2025550106", "primaryPhoneCountryCode": "US", "primaryPhoneCallingCode": "+1", "additionalPhones": []},
            "source": "Career Site", "skillsTags": "React, TypeScript, Design Systems, Accessibility",
            "resumeUrl": "https://example.test/resumes/dorothy-vaughan.pdf",
        })

        requisition_backend = ensure_record(client, report, "requisitions", {
            "name": "REQ-2026-001 Senior Backend Engineer", "jobTitle": "Senior Backend Engineer",
            "department": "Engineering", "location": "Remote", "employmentType": "FULL_TIME",
            "experienceRequirements": "5+ years building production backend systems.",
            "requiredSkills": "Python, FastAPI, PostgreSQL, Docker", "headcount": 1,
            "jobDescription": "Build reliable recruiting-platform APIs and integrations.",
            "postingUrl": "https://jobs.example.test/req-2026-001", "postedAt": now.isoformat(),
            "requisitionStatus": "POSTED",
        })
        requisition_frontend = ensure_record(client, report, "requisitions", {
            "name": "REQ-2026-002 Frontend Engineer", "jobTitle": "Frontend Engineer",
            "department": "Engineering", "location": "Pune", "employmentType": "FULL_TIME",
            "experienceRequirements": "3+ years delivering accessible React applications.",
            "requiredSkills": "React, TypeScript, Vite, CSS", "headcount": 2,
            "jobDescription": "Develop recruiter-facing workflow and analytics interfaces.",
            "requisitionStatus": "APPROVED",
        })
        requisition_datasci = ensure_record(client, report, "requisitions", {
            "name": "REQ-2026-003 Data Scientist", "jobTitle": "Data Scientist",
            "department": "Analytics", "location": "New York", "employmentType": "FULL_TIME",
            "experienceRequirements": "4+ years applied machine learning experience.",
            "requiredSkills": "Python, Pandas, scikit-learn, SQL", "headcount": 1,
            "jobDescription": "Build recruiting-pipeline analytics and predictive models.",
            "postingUrl": "https://jobs.example.test/req-2026-003", "postedAt": (now - timedelta(days=7)).isoformat(),
            "requisitionStatus": "POSTED",
        })
        requisition_devops = ensure_record(client, report, "requisitions", {
            "name": "REQ-2026-004 DevOps Engineer", "jobTitle": "DevOps Engineer",
            "department": "Platform", "location": "Remote", "employmentType": "CONTRACT",
            "experienceRequirements": "5+ years operating production Kubernetes.",
            "requiredSkills": "Kubernetes, Terraform, AWS, GitHub Actions", "headcount": 1,
            "jobDescription": "Own the CI/CD, infrastructure, and observability platform.",
            "requisitionStatus": "JD_PENDING_APPROVAL",
        })
        requisition_intern = ensure_record(client, report, "requisitions", {
            "name": "REQ-2025-099 UX Design Intern", "jobTitle": "UX Design Intern",
            "department": "Design", "location": "Bengaluru", "employmentType": "INTERNSHIP",
            "experienceRequirements": "Portfolio demonstrating accessibility-first design work.",
            "requiredSkills": "Figma, Design Systems, Accessibility", "headcount": 1,
            "jobDescription": "Support recruiter-experience design initiatives.",
            "postingUrl": "https://jobs.example.test/req-2025-099",
            "postedAt": (now - timedelta(days=180)).isoformat(),
            "closedAt": (now - timedelta(days=90)).isoformat(),
            "requisitionStatus": "CLOSED",
        })

        application_ada = ensure_record(client, report, "applications", {
            "name": "Ada Lovelace — Senior Backend Engineer", "candidateId": candidate_ada["id"],
            "requisitionId": requisition_backend["id"], "stage": "DECISION_PENDING",
            "source": "Employee Referral", "appliedAt": (now - timedelta(days=10)).isoformat(),
            "consentStatus": "GRANTED", "parsedResumeSummary": "Strong Python and distributed-systems experience.",
            "decisionRecommendation": "PROCEED", "decisionReason": "Consistently strong technical and collaboration signals.",
        })
        application_grace = ensure_record(client, report, "applications", {
            "name": "Grace Hopper — Frontend Engineer", "candidateId": candidate_grace["id"],
            "requisitionId": requisition_frontend["id"], "stage": "INTERVIEW_SCHEDULED",
            "source": "Career Site", "appliedAt": (now - timedelta(days=5)).isoformat(),
            "consentStatus": "GRANTED", "parsedResumeSummary": "Strong React and accessibility portfolio.",
            "decisionRecommendation": "PENDING", "decisionReason": "Awaiting technical interview.",
        })
        application_margaret = ensure_record(client, report, "applications", {
            "name": "Margaret Hamilton — Senior Backend Engineer", "candidateId": candidate_margaret["id"],
            "requisitionId": requisition_backend["id"], "stage": "REJECTED",
            "source": "Recruiter Sourcing", "appliedAt": (now - timedelta(days=14)).isoformat(),
            "consentStatus": "GRANTED", "parsedResumeSummary": "Excellent systems background; compensation expectations misaligned.",
            "decisionRecommendation": "REJECT", "decisionReason": "Candidate withdrew after compensation discussion.",
        })
        application_katherine = ensure_record(client, report, "applications", {
            "name": "Katherine Johnson — Data Scientist", "candidateId": candidate_katherine["id"],
            "requisitionId": requisition_datasci["id"], "stage": "SCREENING",
            "source": "LinkedIn Sourcing", "appliedAt": (now - timedelta(days=3)).isoformat(),
            "consentStatus": "GRANTED", "parsedResumeSummary": "Strong ML fundamentals; production experience with recommender systems.",
            "decisionRecommendation": "PENDING", "decisionReason": "Recruiter phone screen scheduled.",
        })
        application_alan = ensure_record(client, report, "applications", {
            "name": "Alan Turing — DevOps Engineer", "candidateId": candidate_alan["id"],
            "requisitionId": requisition_devops["id"], "stage": "APPLIED",
            "source": "Referral", "appliedAt": (now - timedelta(days=1)).isoformat(),
            "consentStatus": "PENDING", "parsedResumeSummary": "Deep Kubernetes and Terraform track record across regulated industries.",
            "decisionRecommendation": "PENDING", "decisionReason": "Awaiting consent confirmation before screening.",
        })
        application_dorothy = ensure_record(client, report, "applications", {
            "name": "Dorothy Vaughan — Frontend Engineer", "candidateId": candidate_dorothy["id"],
            "requisitionId": requisition_frontend["id"], "stage": "OFFER",
            "source": "Career Site", "appliedAt": (now - timedelta(days=20)).isoformat(),
            "consentStatus": "GRANTED", "parsedResumeSummary": "Design-systems background; strong accessibility work.",
            "decisionRecommendation": "PROCEED", "decisionReason": "Panel unanimous; offer prepared.",
        })
        application_grace_backend = ensure_record(client, report, "applications", {
            "name": "Grace Hopper — Senior Backend Engineer", "candidateId": candidate_grace["id"],
            "requisitionId": requisition_backend["id"], "stage": "INTERVIEW_COMPLETED",
            "source": "Recruiter Sourcing", "appliedAt": (now - timedelta(days=12)).isoformat(),
            "consentStatus": "GRANTED", "parsedResumeSummary": "Cross-functional engineering leadership; considered as backup pipeline candidate.",
            "decisionRecommendation": "HOLD", "decisionReason": "Strong signals but waiting on primary candidate outcome.",
        })
        application_katherine_withdrawn = ensure_record(client, report, "applications", {
            "name": "Katherine Johnson — Frontend Engineer", "candidateId": candidate_katherine["id"],
            "requisitionId": requisition_frontend["id"], "stage": "REJECTED",
            "source": "Career Site", "appliedAt": (now - timedelta(days=25)).isoformat(),
            "consentStatus": "WITHDRAWN", "parsedResumeSummary": "Candidate opted to focus on data-science pipeline.",
            "decisionRecommendation": "REJECT", "decisionReason": "Candidate withdrew consent to pursue Data Scientist role.",
        })

        interview_ada = ensure_record(client, report, "interviews", {
            "name": "Ada Lovelace — Technical Interview", "applicationId": application_ada["id"],
            "round": "Technical Round", "interviewType": "TECHNICAL", "interviewStatus": "COMPLETED",
            "scheduledAt": (now - timedelta(days=3)).isoformat(), "endedAt": (now - timedelta(days=3) + timedelta(minutes=60)).isoformat(),
            "timezone": "UTC", "durationMinutes": 60,
        })
        ensure_record(client, report, "interviews", {
            "name": "Grace Hopper — Technical Interview", "applicationId": application_grace["id"],
            "round": "Technical Round", "interviewType": "VIDEO", "interviewStatus": "SCHEDULED",
            "scheduledAt": (now + timedelta(days=2)).isoformat(), "timezone": "Asia/Kolkata", "durationMinutes": 45,
        })
        interview_katherine_phone = ensure_record(client, report, "interviews", {
            "name": "Katherine Johnson — Recruiter Screen", "applicationId": application_katherine["id"],
            "round": "Recruiter Screen", "interviewType": "PHONE", "interviewStatus": "CONFIRMED",
            "scheduledAt": (now + timedelta(days=1)).isoformat(),
            "timezone": "America/New_York", "durationMinutes": 30,
        })
        interview_dorothy_onsite = ensure_record(client, report, "interviews", {
            "name": "Dorothy Vaughan — Onsite Panel", "applicationId": application_dorothy["id"],
            "round": "Onsite", "interviewType": "ONSITE", "interviewStatus": "COMPLETED",
            "scheduledAt": (now - timedelta(days=6)).isoformat(),
            "endedAt": (now - timedelta(days=6) + timedelta(hours=4)).isoformat(),
            "timezone": "Asia/Kolkata", "durationMinutes": 240,
        })
        interview_grace_backend = ensure_record(client, report, "interviews", {
            "name": "Grace Hopper — Hiring Manager", "applicationId": application_grace_backend["id"],
            "round": "Hiring Manager", "interviewType": "HIRING_MANAGER", "interviewStatus": "COMPLETED",
            "scheduledAt": (now - timedelta(days=4)).isoformat(),
            "endedAt": (now - timedelta(days=4) + timedelta(minutes=45)).isoformat(),
            "timezone": "UTC", "durationMinutes": 45,
        })
        ensure_record(client, report, "interviews", {
            "name": "Alan Turing — Recruiter Screen", "applicationId": application_alan["id"],
            "round": "Recruiter Screen", "interviewType": "VIDEO", "interviewStatus": "CANCELLED",
            "scheduledAt": (now + timedelta(days=5)).isoformat(),
            "timezone": "Europe/London", "durationMinutes": 30,
        })

        ensure_record(client, report, "evaluations", {
            "name": "Ada Lovelace — AI Technical Evaluation", "interviewId": interview_ada["id"],
            "evaluationType": "INTERVIEW", "authorType": "AGENT", "overallScore": 4.7,
            "recommendation": "PROCEED", "sentiment": "POSITIVE", "evaluationStatus": "FINAL",
            "summary": "Demonstrated strong API design, database reasoning, and production judgement.",
            "strengths": "Python depth; clear trade-off analysis; collaborative communication.",
            "weaknesses": "Could provide more examples of incident response leadership.",
            "promptVersionTag": "interview-v2.0",
        })
        ensure_record(client, report, "evaluations", {
            "name": "Ada Lovelace — Hiring Manager Evaluation", "interviewId": interview_ada["id"],
            "evaluationType": "INTERVIEW", "authorType": "HUMAN", "overallScore": 4.5,
            "recommendation": "PROCEED", "sentiment": "POSITIVE", "evaluationStatus": "FINAL",
            "summary": "Recommended for offer approval.", "strengths": "System design and communication.",
            "weaknesses": "No material concerns.", "promptVersionTag": "human-review",
        })
        ensure_record(client, report, "evaluations", {
            "name": "Katherine Johnson — Resume Screening", "interviewId": interview_katherine_phone["id"],
            "evaluationType": "RESUME", "authorType": "AGENT", "overallScore": 4.2,
            "recommendation": "PROCEED", "sentiment": "POSITIVE", "evaluationStatus": "FINAL",
            "summary": "Resume signals align with Data Scientist requirements.",
            "strengths": "Applied ML experience; strong SQL fundamentals.",
            "weaknesses": "Limited exposure to real-time inference systems.",
            "promptVersionTag": "resume-v1.4",
        })
        ensure_record(client, report, "evaluations", {
            "name": "Dorothy Vaughan — Onsite Panel Evaluation", "interviewId": interview_dorothy_onsite["id"],
            "evaluationType": "INTERVIEW", "authorType": "HUMAN", "overallScore": 4.8,
            "recommendation": "PROCEED", "sentiment": "POSITIVE", "evaluationStatus": "FINAL",
            "summary": "Panel unanimously recommends progressing to offer.",
            "strengths": "Design systems depth; strong accessibility judgement.",
            "weaknesses": "Limited backend integration experience.",
            "promptVersionTag": "human-review",
        })
        ensure_record(client, report, "evaluations", {
            "name": "Grace Hopper — Backend Hiring Manager Evaluation", "interviewId": interview_grace_backend["id"],
            "evaluationType": "INTERVIEW", "authorType": "HUMAN", "overallScore": 3.4,
            "recommendation": "HOLD", "sentiment": "NEUTRAL", "evaluationStatus": "DRAFT",
            "summary": "Strong candidate but not the top choice for this specific requisition.",
            "strengths": "Leadership and mentorship track record.",
            "weaknesses": "Recent hands-on backend work is limited compared to Ada.",
            "promptVersionTag": "human-review",
        })
        ensure_record(client, report, "offers", {
            "name": "Ada Lovelace — Senior Backend Engineer Offer", "applicationId": application_ada["id"],
            "offerStatus": "APPROVED", "salary": 175000.00, "offerCurrency": "USD",
            "startDate": (date.today() + timedelta(days=30)).isoformat(),
            "expiryDate": (date.today() + timedelta(days=10)).isoformat(),
            "termsSummary": "Senior Backend Engineer offer with standard benefits and remote work arrangement.",
        })
        ensure_record(client, report, "offers", {
            "name": "Dorothy Vaughan — Frontend Engineer Offer", "applicationId": application_dorothy["id"],
            "offerStatus": "SENT", "salary": 135000.00, "offerCurrency": "USD",
            "startDate": (date.today() + timedelta(days=45)).isoformat(),
            "expiryDate": (date.today() + timedelta(days=14)).isoformat(),
            "termsSummary": "Frontend Engineer offer with hybrid work option and standard equity grant.",
            "sentAt": (now - timedelta(days=1)).isoformat(),
        })
        ensure_record(client, report, "offers", {
            "name": "Grace Hopper — Senior Backend Engineer Offer", "applicationId": application_grace_backend["id"],
            "offerStatus": "DECLINED", "salary": 168000.00, "offerCurrency": "USD",
            "startDate": (date.today() + timedelta(days=60)).isoformat(),
            "expiryDate": (date.today() - timedelta(days=2)).isoformat(),
            "termsSummary": "Backup Senior Backend Engineer offer extended after primary candidate accepted.",
            "sentAt": (now - timedelta(days=9)).isoformat(),
            "respondedAt": (now - timedelta(days=3)).isoformat(),
            "declineReason": "Accepted an offer at another company before this backup offer was extended.",
        })

        # The rejected applications intentionally have no interview or offer.
        # They validate that optional downstream relationships remain optional.
        report.validated.append("Created records exercise Candidate→Application→Requisition, Application→Interview→Evaluation, and Application→Offer.")
        report.validated.append(f"Optional downstream path preserved for rejected application {application_margaret['id']}.")
        report.validated.append(f"Withdrawn-consent path preserved for rejected application {application_katherine_withdrawn['id']}.")
        report.print()
    finally:
        client.close()


if __name__ == "__main__":
    main_error_boundary(main)
