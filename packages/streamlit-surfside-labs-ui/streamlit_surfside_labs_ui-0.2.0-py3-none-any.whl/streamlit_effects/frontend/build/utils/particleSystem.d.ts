/**
 * Generic particle system for managing particle effects
 */
import { Particle } from "./types";
export declare class ParticleSystem {
    particles: Particle[];
    ctx: CanvasRenderingContext2D;
    constructor(ctx: CanvasRenderingContext2D);
    addParticle(particle: Particle): void;
    update(): void;
    draw(): void;
    clear(): void;
    count(): number;
}
