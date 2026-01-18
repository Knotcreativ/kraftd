import React from 'react'
import { useNavigate } from 'react-router-dom'
import './Legal.css'

export default function TermsOfService() {
  const navigate = useNavigate()

  return (
    <div className="legal-container">
      <div className="legal-header">
        <button className="btn-back" onClick={() => navigate(-1)}>
          ← Back
        </button>
        <h1>Terms of Service</h1>
        <p className="last-updated">Last Updated: January 18, 2026</p>
      </div>

      <div className="legal-content">
        <section>
          <h2>1. Acceptance of Terms</h2>
          <p>
            By accessing and using KraftdIntel ("Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
          </p>
        </section>

        <section>
          <h2>2. Use License</h2>
          <p>
            Permission is granted to temporarily download one copy of the materials (information or software) on KraftdIntel for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:
          </p>
          <ul>
            <li>Modify or copy the materials</li>
            <li>Use the materials for any commercial purpose or for any public display</li>
            <li>Attempt to decompile or reverse engineer any software contained on the Service</li>
            <li>Remove any copyright or other proprietary notations from the materials</li>
            <li>Transfer the materials to another person or "mirror" the materials on any other server</li>
            <li>Violate any applicable laws or regulations</li>
          </ul>
        </section>

        <section>
          <h2>3. Disclaimer</h2>
          <p>
            The materials on KraftdIntel's website are provided on an 'as is' basis. KraftdIntel makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.
          </p>
        </section>

        <section>
          <h2>4. Limitations</h2>
          <p>
            In no event shall KraftdIntel or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on KraftdIntel's website, even if KraftdIntel or a KraftdIntel authorized representative has been notified orally or in writing of the possibility of such damage.
          </p>
        </section>

        <section>
          <h2>5. Accuracy of Materials</h2>
          <p>
            The materials appearing on KraftdIntel could include technical, typographical, or photographic errors. KraftdIntel does not warrant that any of the materials on the Service are accurate, complete, or current. KraftdIntel may make changes to the materials contained on the Service at any time without notice.
          </p>
        </section>

        <section>
          <h2>6. Materials on the Service</h2>
          <p>
            KraftdIntel has not reviewed all of the sites linked to its website and is not responsible for the contents of any such linked site. The inclusion of any link does not imply endorsement by KraftdIntel of the site. Use of any such linked website is at the user's own risk.
          </p>
        </section>

        <section>
          <h2>7. Modifications</h2>
          <p>
            KraftdIntel may revise these Terms of Service for the Service at any time without notice. By using this Service, you are agreeing to be bound by the then current version of these Terms of Service.
          </p>
        </section>

        <section>
          <h2>8. Governing Law</h2>
          <p>
            These Terms and Conditions are governed by and construed in accordance with the laws of the United Arab Emirates, and you irrevocably submit to the exclusive jurisdiction of the courts located in that location.
          </p>
        </section>

        <section>
          <h2>9. User Accounts</h2>
          <p>
            If you create an account on the Service, you are responsible for maintaining the confidentiality of your account information and password. You agree to accept responsibility for all activities that occur under your account. You must notify us immediately of any unauthorized use of your account or any other breaches of security.
          </p>
        </section>

        <section>
          <h2>10. Content and Conduct</h2>
          <p>
            You agree that you will not post, upload, or transmit through the Service any material that:
          </p>
          <ul>
            <li>Is unlawful, threatening, abusive, defamatory, obscene, or otherwise objectionable</li>
            <li>Violates any intellectual property rights or privacy rights</li>
            <li>Contains software viruses or malicious code</li>
            <li>Impersonates any person or entity</li>
            <li>Is commercially exploitative or deceptive</li>
          </ul>
        </section>

        <section>
          <h2>11. Limitation of Liability</h2>
          <p>
            To the fullest extent permitted by applicable law, in no event shall KraftdIntel be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits or revenues, whether or not foreseeable, whether or not KraftdIntel has been advised of the possibility of such damages, and arising from any cause whatsoever (including negligence, breach of contract, strict liability, or tort) relating to this Service or the materials.
          </p>
        </section>

        <section>
          <h2>12. Contact Information</h2>
          <p>
            If you have questions about these Terms of Service, please contact us at:
          </p>
          <p>
            <strong>KraftdIntel Support</strong><br />
            Email: support@kraftdintel.com<br />
            Location: United Arab Emirates
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
