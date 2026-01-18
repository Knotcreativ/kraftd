import React from 'react'
import { useNavigate } from 'react-router-dom'
import './Legal.css'

export default function PrivacyPolicy() {
  const navigate = useNavigate()

  return (
    <div className="legal-container">
      <div className="legal-header">
        <button className="btn-back" onClick={() => navigate(-1)}>
          ← Back
        </button>
        <h1>Privacy Policy</h1>
        <p className="last-updated">Last Updated: January 18, 2026</p>
      </div>

      <div className="legal-content">
        <section>
          <h2>1. Introduction</h2>
          <p>
            KraftdIntel ("we", "us", "our", or "Company") operates the KraftdIntel website and application (the "Service"). This page informs you of our policies regarding the collection, use, and disclosure of personal data when you use our Service and the choices you have associated with that data.
          </p>
        </section>

        <section>
          <h2>2. Information Collection and Use</h2>
          <p>We collect several different types of information for various purposes to provide and improve our Service to you.</p>

          <h3>Types of Data Collected:</h3>
          <ul>
            <li><strong>Personal Data:</strong> Email address, name, organization name, password (hashed)</li>
            <li><strong>Usage Data:</strong> Browser type, IP address, pages visited, time and date of visits, time spent on pages</li>
            <li><strong>Document Data:</strong> Files you upload, extracted data, processing results</li>
            <li><strong>Cookies and Tracking:</strong> Session tokens, authentication cookies</li>
          </ul>
        </section>

        <section>
          <h2>3. Use of Data</h2>
          <p>KraftdIntel uses the collected data for various purposes:</p>
          <ul>
            <li>To provide and maintain the Service</li>
            <li>To notify you about changes to our Service</li>
            <li>To provide customer support</li>
            <li>To gather analysis or valuable information so that we can improve the Service</li>
            <li>To monitor the usage of the Service</li>
            <li>To detect, prevent and address technical and security issues</li>
            <li>To provide you with news, special offers and general information about our products or services</li>
          </ul>
        </section>

        <section>
          <h2>4. Security of Data</h2>
          <p>
            The security of your data is important to us but remember that no method of transmission over the Internet or method of electronic storage is 100% secure. While we strive to use commercially acceptable means to protect your Personal Data, we cannot guarantee its absolute security.
          </p>
          <p>
            KraftdIntel implements the following security measures:
          </p>
          <ul>
            <li>JWT-based authentication with token expiration</li>
            <li>bcrypt password hashing (never plain text)</li>
            <li>HTTPS/TLS encryption for data in transit</li>
            <li>Rate limiting to prevent abuse</li>
            <li>Multi-tenant data isolation</li>
            <li>Azure security best practices</li>
          </ul>
        </section>

        <section>
          <h2>5. Document Processing and Retention</h2>
          <p>
            When you upload documents to our Service:
          </p>
          <ul>
            <li>Documents are processed to extract structured data</li>
            <li>Original files are stored securely in cloud storage</li>
            <li>Extracted data is retained in our database</li>
            <li>You can delete your documents and data from your dashboard</li>
            <li>Deleted data is removed within 30 days</li>
          </ul>
        </section>

        <section>
          <h2>6. Third-Party Service Providers</h2>
          <p>
            We may employ third-party companies and individuals to facilitate our Service ("Service Providers"), to provide the Service on our behalf, or to perform Service-related services including:
          </p>
          <ul>
            <li>Microsoft Azure (cloud infrastructure)</li>
            <li>Azure Document Intelligence (document processing)</li>
            <li>Azure OpenAI (AI processing)</li>
            <li>Application Insights (analytics)</li>
          </ul>
          <p>
            These third parties have access to your Personal Data only to perform these tasks on our behalf and are obligated not to disclose or use it for any other purpose.
          </p>
        </section>

        <section>
          <h2>7. Children's Privacy</h2>
          <p>
            Our Service does not address anyone under the age of 18. We do not knowingly collect personally identifiable information from children under 18. If we discover that a child under 18 has provided us with Personal Data, we will delete such information and terminate the child's account immediately.
          </p>
        </section>

        <section>
          <h2>8. Changes to This Privacy Policy</h2>
          <p>
            We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last Updated" date at the top of this Privacy Policy.
          </p>
        </section>

        <section>
          <h2>9. Contact Us</h2>
          <p>
            If you have any questions about this Privacy Policy, please contact us:
          </p>
          <p>
            <strong>KraftdIntel Privacy Team</strong><br />
            Email: privacy@kraftdintel.com<br />
            Location: United Arab Emirates
          </p>
        </section>

        <section>
          <h2>10. Your Rights</h2>
          <p>
            Depending on your location, you may have certain rights regarding your personal data:
          </p>
          <ul>
            <li><strong>Right to Access:</strong> You can request a copy of the data we hold about you</li>
            <li><strong>Right to Rectification:</strong> You can correct inaccurate data</li>
            <li><strong>Right to Erasure:</strong> You can request deletion of your data</li>
            <li><strong>Right to Restrict Processing:</strong> You can limit how we use your data</li>
            <li><strong>Right to Portability:</strong> You can request your data in a portable format</li>
          </ul>
          <p>
            To exercise these rights, please contact us at privacy@kraftdintel.com.
          </p>
        </section>
      </div>

      <div className="legal-footer">
        <button className="btn-secondary" onClick={() => navigate(-1)}>
          Back to Login
        </button>
      </div>
    </div>
  )
}
