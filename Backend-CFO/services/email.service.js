const nodemailer = require('nodemailer');

class EmailService {
    constructor() {
        this.transporter = nodemailer.createTransport({
            host: process.env.EMAIL_HOST,
            port: process.env.EMAIL_PORT,
            secure: false,
            auth: {
                user: process.env.EMAIL_USER,
                // → No-reply Gmail account
                pass: process.env.EMAIL_PASSWORD,
                // → 16-char App Password (spaces don't matter)
            }
        });
    }

    async sendEmail(to, subject, text, html = null) {
        const mailOptions = {
            from: process.env.DEFAULT_FROM_EMAIL,
            // → Shown in email
            to,
            subject,
            text,
            html: html || text
        };

        try {
            const info = await this.transporter.sendMail(mailOptions);
            console.log('Email sent:', info.messageId);
            return { success: true, messageId: info.messageId };
        } catch (error) {
            console.error('Email error:', error);
            throw error;
        }
    }

    async sendPasswordResetEmail(email, resetToken) {
        const subject = 'Password Reset Request';
        // replace localhost with your frontend domain
        const resetUrl = `http://localhost:3000/reset-password?token=${resetToken}`;
        const text = `You requested a password reset. Click the link to reset your password: ${resetUrl}`;
        const html = `
            <p>You requested a password reset.</p>
            <p>Click the link below to reset your password:</p>
            <a href="${resetUrl}">${resetUrl}</a>
            <p>If you didn't request this, please ignore this email.</p>
        `;

        return await this.sendEmail(email, subject, text, html);
    }
}

module.exports = new EmailService();
